# Uplift Analysis
> Analysis of Firefox uplifts.

The 'all_bugs' directory holds the analysis of uplifts inducing bugs fixed by generic commits.
The 'uplift_bugs' directory holds the analysis of uplifts inducing bugs fixed by other uplifts.

### What uplifts are ###

Firefox follows a train model, XXX.

Uplifts are changes that skip the stabilization phase on one or more channels and go straight from a development channel to a more stable one. For example, taking a patch that fixes a bug in the Nightly version and applying it to the Beta version.

The more stable the branch, the higher the bar for approval of an uplift should be, in theory. See the rules for the uplifts for reference [https://wiki.mozilla.org/Release_Management/Uplift_rules].

### Why are we interested in uplifts? ###

The Firefox release process has been designed to balance new feature work and quality. Uplifting subverts this process and reduces the amount of stabilization time available for the feature, but it's needed in some cases for high-value features and bug fixes.
Given the reduction of stabilization time, the risk associated to uplifts is much higher than normal changes.
We are interested in understanding which uplifts caused regressions and why, where/when uplifts succeed/fail the most, and, last but not least, how to improve the uplift process.

### Research questions ###
- RQ1: What kind of patches were uplifted?
- RQ2: Why some uplifted patches failed?
- RQ3: How can we improve the uplifting process?
