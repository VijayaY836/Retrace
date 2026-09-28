# The RETRACE method

## 1. Every conclusion is a dated belief
A belief is what the team concluded after an experiment, with its date and source experiment, e.g. "Gamification hurts onboarding" (after EXP-07, March 2024).

## 2. Evidence quality
- **Inconclusive**: fewer than 2,000 users. Never builds a conclusion.
- **Caution**: ran during an outage or a sale. Treated as unreliable.
- **No effect**: p ≥ 0.05 with enough users counts as real evidence of no effect.

## 3. Clean comparisons
Two experiments in the same area and metric that differ in **exactly one condition** form a clean comparison. Only clean comparisons can isolate a factor. Comparisons that differ in two or more conditions are **confounded** and are shown as supporting context only.

## 4. Belief status
- **Held up**: later evidence agrees.
- **Challenged**: later evidence disagrees, but no clean comparison isolates the cause.
- **Revised**: a clean comparison contradicts the belief, or shows it only holds under some conditions.
- **Weak basis**: the belief came from an inconclusive experiment.
- **Untested since**: no later evidence.

## 5. Then vs now
An old result may no longer apply if a condition that clean comparisons show to matter has changed since (e.g. onboarding went from 7 to 3 steps).

## 6. What haven't we tested?
For each feature area, list every combination of the conditions that matter. Mark each as tested, inconclusive, planned or never tested. Rank untested combinations by how many clean comparisons they would complete. Phrase suggestions as open questions, never predictions.
