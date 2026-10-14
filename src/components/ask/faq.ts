// The fallback, as data. These are the questions the endpoint is asked most
// obviously, answered from the page itself — no model involved, so they are
// what a visitor sees when the endpoint is slow, rate-limited, out of its
// daily allowance, or simply not reached because JavaScript is off.
//
// Each one points at the section that carries the evidence: the fallback has
// to satisfy the same rule as a generated answer, which is that nothing is
// asserted without somewhere to go and check it.

import type { UIKey } from "../../i18n/ui";

export interface FaqEntry {
  id: string;
  question: UIKey;
  answer: UIKey;
  /** Section anchor on the same page. */
  anchor: string;
}

export const FAQ: readonly FaqEntry[] = [
  {
    id: "chain",
    question: "ask.faq.chain.q",
    answer: "ask.faq.chain.a",
    anchor: "system",
  },
  {
    id: "status",
    question: "ask.faq.status.q",
    answer: "ask.faq.status.a",
    anchor: "project-lamula",
  },
  {
    id: "phd",
    question: "ask.faq.phd.q",
    answer: "ask.faq.phd.a",
    anchor: "research",
  },
  {
    id: "team",
    question: "ask.faq.team.q",
    answer: "ask.faq.team.a",
    anchor: "experience",
  },
  {
    id: "teaching",
    question: "ask.faq.teaching.q",
    answer: "ask.faq.teaching.a",
    anchor: "experience",
  },
  {
    id: "contact",
    question: "ask.faq.contact.q",
    answer: "ask.faq.contact.a",
    anchor: "contact",
  },
] as const;
