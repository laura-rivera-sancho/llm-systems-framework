# Business case: feedback triage for a B2B SaaS team

## Decision context

Product and customer-facing teams hear about friction through support tickets, surveys, onboarding conversations, and product requests. Each channel captures a different part of the customer experience. When the feedback is read and categorized by hand, teams can struggle to compare it consistently, spot repeated issues across channels, and connect a specific comment to a useful next step.

The decision this project explores is narrow: **how can a team organize incoming feedback into reviewable signals that help people decide what to investigate or route next?** It does not attempt to decide whether to contact a customer, change a product, or allocate engineering capacity without human review.

## Proposed workflow

For each feedback record, the workflow asks a language model to return a controlled sentiment and issue category, a concise theme, a cautious root-cause hypothesis, an urgency level, a suggested follow-up, and a short excerpt from the source comment. The application validates the response structure and checks that the excerpt occurs in the original comment. A local dashboard then groups the saved results for exploration.

The output is intended to support triage, not replace it. A product or customer-experience owner should be able to open the original comment, verify the evidence, correct the classification, and decide what action—if any—is appropriate.

## Value hypothesis

If the workflow is accurate enough for a defined use case, it could reduce the effort required to create a first-pass view of recurring feedback and make handoffs more consistent. That benefit is a hypothesis, not a measured result. The current project has no real customer data, operational baseline, time study, or evidence of downstream business impact.

The value should be tested against the current process using measures such as:

- reviewer time per record and time to prepare a cross-channel summary;
- agreement between independent reviewers and the model on sentiment and category;
- category-level precision and recall, with sample size and class coverage reported;
- rate of valid, source-grounded evidence excerpts;
- human correction and escalation rates, broken down by category and feedback source;
- whether teams make faster or better-supported decisions, measured in a separately designed pilot.

Accuracy alone would not establish business value. A model could classify common categories well while missing rare, high-impact issues, or produce plausible summaries that reviewers still need to rewrite.

## What the prototype demonstrates

The repository uses 120 deterministic fictional feedback records. The Python pipeline sends only the comment text to Gemini, requests structured output with controlled labels, checks the result and its supporting excerpt, caches successful classifications, and saves progress so a run can resume. The Streamlit dashboard can be opened without calling the API and can display the saved synthetic results. A separate blind-review workflow supports human labels and comparison with model predictions.

These capabilities demonstrate an end-to-end implementation pattern. They do not establish production performance, representative customer trends, lower support costs, improved retention, or a reduction in manual work. The existing human-labeled sample is too small for a reliable quality estimate.

## Operating boundaries and risks

- **Unsupported inference:** A plausible category or root cause may still be wrong. Require evidence review and make correction straightforward.
- **Sensitive input:** Real support text can contain personal, financial, or account details. The prototype is for synthetic or properly de-identified text; a real deployment would require access, retention, and provider data-handling controls.
- **Taxonomy mismatch:** A fixed category list may not reflect how a particular organization works. Define ownership and change control for labels before a pilot.
- **Uneven error costs:** Missing a rare security or reliability issue can matter more than misclassifying a routine feature request. Measure errors by class and define escalation rules.
- **Model and service variability:** Model versions, quotas, latency, and response quality can change. Track version, usage, failures, and review outcomes; retain a manual fallback.
- **Synthetic-data bias:** Repeated scenarios and balanced construction make the bundled data useful for repeatable demonstrations, not for estimating issue prevalence or customer sentiment.

## Evidence required before a real pilot

1. Agree on the triage decision, taxonomy, owners, and actions the output is allowed to inform.
2. Define a privacy and retention process for feedback before any real text is sent to an external model.
3. Build a representative, human-labeled evaluation set with adequate examples of important categories, including rare high-impact issues.
4. Use independent reviewers, resolve disagreements under a documented protocol, and keep reviewers blind to model output during initial labeling.
5. Compare the assisted workflow with the current process on quality, reviewer effort, escalation, and decision usefulness.
6. Set acceptance thresholds and rollback conditions before any operational use.

## Scope statement

This is a synthetic-data portfolio prototype. Its business case is the problem framing and a testable value hypothesis—not a claim that the model has delivered customer, financial, or productivity outcomes. Any future case study should preserve that distinction and add measured results only after a properly governed pilot.
