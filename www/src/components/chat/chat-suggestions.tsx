import { FileText, HelpCircle, PieChart, Vote, Code, AlertCircle } from "lucide-react";

const optimismSuggestions = [
  {
    icon: <FileText size={20} />,
    label: "Explain recent proposal",
    value: "Can you explain the most recent Optimism governance proposal?",
  },
  {
    icon: <Vote size={20} />,
    label: "How to vote",
    value: "How can I participate in voting on Optimism governance proposals?",
  },
  {
    icon: <PieChart size={20} />,
    label: "OP token distribution",
    value: "Can you give me an overview of the OP token distribution?",
  },
  {
    icon: <HelpCircle size={20} />,
    label: "Optimism Collective",
    value: "What is the Optimism Collective and how does it work?",
  },
] as const;

const cowSuggestions = [
  {
    icon: <Code size={20} />,
    label: "buyAmount and slippage",
    value: "How do I set buyAmount with slippage when creating an order?",
  },
  {
    icon: <Code size={20} />,
    label: "Token approval (gasless)",
    value: "How do I set token approval via ABI for a gasless swap?",
  },
  {
    icon: <HelpCircle size={20} />,
    label: "Fast vs optimal quote",
    value: "When should I use fast vs optimal quoting?",
  },
  {
    icon: <AlertCircle size={20} />,
    label: "Error troubleshooting",
    value: "What does InsufficientBalance mean and how do I fix it?",
  },
] as const;

const brand = typeof process !== "undefined" ? process.env.NEXT_PUBLIC_BRAND : "";
export const suggestions = brand === "cow" ? cowSuggestions : optimismSuggestions;
