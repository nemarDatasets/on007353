[![DOI](https://img.shields.io/badge/DOI-10.82901%2Fnemar.on007353-blue)](https://doi.org/10.82901/nemar.on007353)

Human action recognition is a core component of social cognition, engaging spatially distributed and temporally evolving neural responses that encode visual information and infer intention. To map the brain’s spatial organization supporting this process, we previously released the Human Action Dataset (HAD), a functional magnetic resonance imaging (fMRI) resource. However, fMRI’s limited temporal resolution constrains its ability to capture rapid neural dynamics. Here, we present the HAD-MEEG dataset, which extends HAD-fMRI, leveraging the millisecond-level temporal resolution of magnetoencephalography (MEG) and electroencephalography (EEG). HAD-MEEG were recorded in the same participants and with the same stimuli as HAD-fMRI, in which 30 participants viewed 21,600 video clips spanning 180 categories of human action. By integrating the temporal precision of M/EEG with the spatial precision of fMRI, HAD enables comprehensive spatiotemporal investigation of the neural mechanisms underlying human action recognition.

## Stimuli

`stimuli/` holds the 21,600 clips (180 action classes x 120) as deposited by the authors: HACS clips cut from YouTube videos
(third-party content). File names give the YouTube id and the start second, `v_<class>_id_<YouTube id>_start_<s>_label_1.mp4`.

Added 2026-10-08 (metadata only, no media added):
- `stimuli/stimuli.tsv` + `stimuli.json`: one row per clip with its path, YouTube id, start, duration, frame rate, size,
  frame count, audio track and SHA-256 (all clips 256 x 256 pixels, 2.0-2.1 s; 14 clips have no audio stream).
- A `stim_id` column in every `sub-*_ses-{eeg,meg}_task-action_run-*_events.tsv`: the clip shown at each `video on` event
  (its file name without `.mp4`; n/a on other rows), described in each run's `_events.json`; the path is in
  `stimuli/stimuli.tsv`. (BIDS `stim_file` is not used because bids-validator rejects the spaces in this dataset's class
  folder names inside `stim_file` paths.)

How the event-to-clip mapping was obtained: the released events carry no clip identity, and
`derivatives/detailed_events` gives the class and YouTube id per trial but not the start second; 665 of the 20,160 EEG
trials (3.3 %) were therefore ambiguous (one YouTube video cut at two or three starts). The sibling dataset HAD-fMRI
(OpenNeuro ds004488 2.0.1, same stimuli) has a `stim_file` column in its events. Every HAD-MEEG session (28 EEG, 30 MEG)
presented exactly one HAD-fMRI participant's 720-clip list in the same order (58/58 sessions; 720/720 YouTube ids equal
position by position; e.g. EEG sub-01 = fMRI sub-22, MEG sub-01 = fMRI sub-01). Each `video on` event therefore maps to its
clip by position: 20,160/20,160 EEG and 21,600/21,600 MEG trials, all files present under `stimuli/`; the 19,495 EEG trials
that were unambiguous before agree 19,495/19,495. Naming note: HAD-fMRI writes class folders with `_`
(`Drum_corps/`), this dataset with spaces (`Drum corps/`).

To check the mapping yourself: `python code/check_stim_id.py <ds004488>` (a clone of OpenNeuro ds004488 2.0.1; its events
are plain git files). For every session it finds the one HAD-fMRI list with the same order, then checks each `video on`
row against that list position by position and against the class and YouTube id in `derivatives/detailed_events`. On
this version: 58/58 sessions match exactly one list, 41,760/41,760 rows pass (40,388 also unique from detailed_events
alone, 1,372 resolved only by the order), 0 fail.
