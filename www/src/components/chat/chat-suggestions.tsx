import { Code, HelpCircle, AlertCircle } from "lucide-react";

export const suggestions = [
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
