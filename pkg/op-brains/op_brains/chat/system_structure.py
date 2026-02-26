from typing import Tuple, Any, Callable, List
from op_brains.chat.apis import access_APIs
import pandas as pd

import re

# Match reference citations like [1], [2], "reference [1]", "ref [2]". Used to return only cited URLs.
REF_CITATION_RE = re.compile(r"\b(?:reference|ref|see|below)\s*\[(\d+)\]|(?<!\w)\[(\d+)\](?=\s*(?:and|,|\.|\)|below|$))", re.IGNORECASE)


def _cited_reference_numbers(answer_text: str, max_ref: int = 10) -> List[int]:
    """Extract reference numbers cited in the answer (e.g. [1], [2]) in order of first appearance."""
    if not answer_text:
        return []
    numbers_ordered = []
    seen = set()
    for m in REF_CITATION_RE.finditer(answer_text):
        n = int(m.group(1) or m.group(2))
        if 1 <= n <= max_ref and n not in seen:
            seen.add(n)
            numbers_ordered.append(n)
    # Also catch "References: [1] [2] [3]" at the end
    refs_section = re.search(r"references?\s*:\s*((?:\[\d+\]\s*)+)", answer_text, re.IGNORECASE)
    if refs_section:
        for m in re.finditer(r"\[(\d+)\]", refs_section.group(1)):
            num = int(m.group(1))
            if 1 <= num <= max_ref and num not in seen:
                seen.add(num)
                numbers_ordered.append(num)
    return numbers_ordered


def _renumber_citations_to_sequential(answer_text: str, cited_ordered: List[int]) -> str:
    """Rewrite citation numbers so they are sequential [1], [2], [3], ... matching url_supporting order."""
    if not cited_ordered:
        return answer_text
    old_to_new = {old: i for i, old in enumerate(cited_ordered, start=1)}
    return _renumber_citations_with_mapping(answer_text, old_to_new)


def _renumber_citations_with_mapping(answer_text: str, old_to_new: dict) -> str:
    """Rewrite citation numbers using old_to_new mapping. Replace from largest old first to avoid collisions."""
    if not old_to_new:
        return answer_text
    for old in sorted(old_to_new.keys(), reverse=True):
        new = old_to_new[old]
        if old != new:
            answer_text = re.sub(r"\[" + str(old) + r"\]", "[" + str(new) + "]", answer_text)
    # Remove any [n] that are not in mapping (e.g. model cited [11] but we only have 10 sources)
    return answer_text


class RAGSystem:
    REASONING_LIMIT: int
    models_to_use: list
    retriever: Callable
    context_filter: Callable
    system_prompt_preprocessor: Callable
    system_prompt_responder: Callable

    llm: list = []
    number_of_models: int = 2

    def __init__(self, **kwargs):
        self.REASONING_LIMIT = kwargs.get("REASONING_LIMIT") or kwargs.get("reasoning_limit", 3)
        self.models_to_use = kwargs.get("models_to_use")
        self.retriever = kwargs.get("retriever")
        self.context_filter = kwargs.get("context_filter")
        self.system_prompt_preprocessor = kwargs.get("system_prompt_preprocessor")
        self.system_prompt_responder = kwargs.get("system_prompt_responder")

        assert len(self.models_to_use) == self.number_of_models

        for m in self.models_to_use:
            m, pars = m
            self.llm += [access_APIs.get_llm(m, **pars)]

    def query_preprocessing_LLM(
        self, query: str, memory: list, LLM: Any = None
    ) -> Tuple[bool, str | Tuple[str, list]]:
        if LLM is None:
            LLM = self.llm[0]

        output_LLM = self.system_prompt_preprocessor(
            LLM, QUERY=query, CONVERSATION_HISTORY=memory
        )

        print(output_LLM)

        if not output_LLM["needs_info"]:
            return False, output_LLM["answer"]
        else:
            user_knowledge = output_LLM["expansion"]["user_knowledge"]
            type_search = output_LLM["expansion"]["type_search"]

            keywords = output_LLM["expansion"]["keywords"]
            keywords = [{"keyword": k} for k in keywords]

            questions = output_LLM["expansion"]["questions"]
            questions = [{"question": q} for q in questions]

            return True, (user_knowledge, keywords + questions, type_search)

    def responder_LLM(
        self,
        query: str,
        context: str,
        user_knowledge: str,
        summary_of_explored_contexts: str,
        final: bool = False,
        LLM: Any = None,
    ):  # -> Tuple[str|list, bool]:
        if LLM is None:
            LLM = self.llm[1]

        output_LLM = self.system_prompt_responder(
            LLM,
            final=final,
            QUERY=query,
            CONTEXT=context,
            USER_KNOWLEDGE=user_knowledge,
            SUMMARY_OF_EXPLORED_CONTEXTS=summary_of_explored_contexts,
        )

        if output_LLM is None:
            return ("", [], ""), False

        knowledge_summary = output_LLM["knowledge_summary"]
        if output_LLM["answer"] is not None:
            output_LLM["answer"]["url_supporting"].extend(
                [k["url_supporting"].strip() for k in knowledge_summary]
            )
            output_LLM["answer"]["url_supporting"] = list(
                set(output_LLM["answer"]["url_supporting"])
            )
            return output_LLM["answer"], True
        else:
            new_questions = output_LLM["search"]["questions"]
            new_questions = [{"question": q} for q in new_questions]
            type_search = output_LLM["search"]["type_search"]
            return [knowledge_summary, new_questions, type_search], False

    async def predict(
        self,
        query: str,
        contexts_df: pd.DataFrame,
        memory: list = [],
        verbose: bool = False,
    ) -> str:
        needs_info, preprocess_reasoning = self.query_preprocessing_LLM(
            query, memory=memory
        )
        history_reasoning = {
            "query": query,
            "needs_info": needs_info,
            "preprocess_reasoning": preprocess_reasoning,
            "reasoning": {},
        }
        if verbose:
            print(
                f"-------------------\nQuery: {query}\nNeeds info: {needs_info}\nPreprocess reasoning: {preprocess_reasoning}\n"
            )
        if needs_info:
            is_enough = False
            explored_contexts_urls = []
            user_knowledge, questions, type_search = preprocess_reasoning
            result = "", questions, type_search
            reasoning_level = 0
            # Hard cap so we never loop indefinitely if responder never returns answer
            max_level = max(self.REASONING_LIMIT + 2, 5)

            while not is_enough:
                if reasoning_level >= max_level:
                    result = {"answer": "I couldn't find enough information to answer. Please try rephrasing or ask something more specific.", "url_supporting": []}
                    is_enough = True
                    if verbose:
                        print(f"-------Hit max reasoning level {max_level}, returning fallback.\n")
                    break

                summary_of_explored_contexts, questions, type_search = result
                try:
                    questions = [{"query": query}] + questions
                except Exception:
                    pass

                context_dict = {
                    list(q.values())[0]: await self.retriever(
                        q, reasoning_level=reasoning_level
                    )
                    for q in questions
                }
                # context_dict = {c.metadata['url']:c for cc in context_list for c in cc}

                context, context_urls = await self.context_filter(
                    context_dict,
                    explored_contexts_urls,
                    contexts_df,
                    query,
                    type_search,
                )
                explored_contexts_urls.extend(context_urls)

                if verbose:
                    print(
                        f"-------Reasoning level {reasoning_level}\nExploring Context URLS: {context_urls}"
                    )

                result, is_enough = self.responder_LLM(
                    query,
                    context,
                    user_knowledge,
                    summary_of_explored_contexts,
                    final=reasoning_level > self.REASONING_LIMIT,
                )

                # Use only the references actually cited in the answer: map [1], [2] to context_urls by index (1-based).
                # Renumber citations so they are sequential [1], [2], ... matching url_supporting (deduped URLs).
                if is_enough and isinstance(result, dict) and result.get("url_supporting") is not None and context_urls:
                    answer_text = result.get("answer") or ""
                    cited = _cited_reference_numbers(answer_text)
                    if cited:
                        # Build deduped ordered_urls and map each cited index to its 1-based rank in that list.
                        ordered_urls = []
                        seen = set()
                        for i in cited:
                            if 1 <= i <= len(context_urls):
                                u = context_urls[i - 1]
                                if u and u not in seen:
                                    seen.add(u)
                                    ordered_urls.append(u)
                        result["url_supporting"] = ordered_urls
                        url_to_rank = {u: r for r, u in enumerate(ordered_urls, start=1)}
                        old_to_new = {}
                        for i in cited:
                            if 1 <= i <= len(context_urls):
                                u = context_urls[i - 1]
                                if u:
                                    old_to_new[i] = url_to_rank[u]
                        answer_text = _renumber_citations_with_mapping(answer_text, old_to_new)
                        n_refs = len(ordered_urls)
                        # Remove orphan citation markers (e.g. [11] when we only have 3 URLs)
                        for orphan in range(n_refs + 1, 20):
                            answer_text = re.sub(r"\[" + str(orphan) + r"\]", "", answer_text)
                        # Normalize "References: ..." line to exactly [1] [2] ... so it matches url_supporting
                        refs_line = " ".join(f"[{r}]" for r in range(1, n_refs + 1))
                        if re.search(r"\breferences?\s*:", answer_text, re.IGNORECASE):
                            answer_text = re.sub(
                                r"\breferences?\s*:\s*(?:\[\d+\]\s*)*",
                                f"References: {refs_line}",
                                answer_text,
                                flags=re.IGNORECASE,
                                count=1,
                            )
                        elif n_refs > 0:
                            answer_text = answer_text.rstrip() + f"\n\nReferences: {refs_line}"
                        result["answer"] = answer_text
                    else:
                        result["url_supporting"] = list(result.get("url_supporting") or [])[:6]

                # If responder failed (e.g. LLM error) but we have context, return a fallback so we don't loop
                if not is_enough and context and isinstance(result, (list, tuple)) and len(result) == 3 and result[0] == "" and result[1] == []:
                    result = {"answer": "I found relevant documentation but couldn't generate a full answer. Please try rephrasing or ask a more specific question.", "url_supporting": list(context_urls)}
                    is_enough = True
                    if verbose:
                        print("-------Responder returned empty with context; using fallback.\n")

                if verbose:
                    print(f"-------Result: {result}\n")
                    if is_enough:
                        print("END!!!\n")

                reasoning_level += 1
                history_reasoning["reasoning"][reasoning_level] = {
                    "context": context,
                    "result": result,
                }
            answer = result
        else:
            answer = {"answer": preprocess_reasoning, "url_supporting": []}
        history_reasoning["answer"] = answer
        return history_reasoning
