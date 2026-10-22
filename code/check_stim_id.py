#!/usr/bin/env python3
"""Check the stim_id column of every task-action events.tsv of on007353 (HAD-MEEG) against two sources.

usage: python code/check_stim_id.py <ds004488>

<ds004488> is a copy of OpenNeuro ds004488 (HAD-fMRI) 2.0.1 that has at least its task-action events, e.g.
    git clone -b 2.0.1 https://github.com/OpenNeuroDatasets/ds004488.git
(the events are plain git files, no annex download is needed). Run it from the root of this dataset.

What it checks, for each EEG and MEG session of each participant:
  1. Presentation order. The session's 'video on' rows, in run order, are compared with the clip list of every
     ds004488 participant (its stim_file column over ses-action*, run order). The session must equal exactly one
     list over all its trials (720 clips per complete session).
  2. Row by row. Each 'video on' row's stim_id must be the file name, without '.mp4', of the ds004488 clip at the
     same position (ds004488 writes class folders with '_' where this dataset uses spaces; that is the only change).
  3. Independent cross-check. derivatives/detailed_events/sub-XX_events.tsv (written by the dataset authors) gives
     the class and YouTube id of every trial. Each stim_id must name that class and that YouTube id. Where the
     (class, YouTube id) pair has more than one file in stimuli/ (different start times), detailed_events alone
     cannot tell which one was shown; those rows are counted as 'resolved only by the order'.
  4. Every stim_id is a row of stimuli/stimuli.tsv, and every row that is not 'video on' has stim_id n/a.
It prints the counts and exits 1 if any row fails.
"""
import collections
import csv
import glob
import os
import re
import sys


def read_tsv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def norm(s):
    return s.replace(" ", "_")


def main(ds004488):
    stim = {r["stim_id"]: r for r in read_tsv("stimuli/stimuli.tsv")}
    by_pair = collections.Counter()
    for sid in stim:
        m = re.match(r"v_(.+)_id_(.+)_start_[0-9.]+_label_\d+$", sid)
        by_pair[(norm(m.group(1)), m.group(2))] += 1

    # ds004488: one clip list per participant (all ses-action* runs in order)
    fmri = {}
    for sub in sorted(glob.glob(os.path.join(ds004488, "sub-*"))):
        seq = []
        for p in sorted(glob.glob(os.path.join(sub, "ses-action*", "func", "*_task-action_run-*_events.tsv"))):
            seq += [norm(os.path.basename(r["stim_file"]))[:-4] for r in read_tsv(p) if r.get("stim_file", "n/a") != "n/a"]
        fmri[os.path.basename(sub)] = seq
    if not fmri:
        sys.exit(f"no ds004488 task-action events under {ds004488}")

    c = collections.Counter()
    problems = []
    sessions = {}
    for ev in sorted(glob.glob("sub-*/ses-*/*/sub-*_ses-*_task-action_run-*_events.tsv")):
        m = re.match(r"sub-(\d+)/ses-(eeg|meg)/.*_run-(\d+)_events\.tsv$", ev)
        sessions.setdefault((m.group(1), m.group(2)), []).append((int(m.group(3)), ev))

    for (sub, ses), runs in sorted(sessions.items()):
        rows = []
        for _, ev in sorted(runs):
            c["events_files"] += 1
            for i, r in enumerate(read_tsv(ev), 2):
                if "stim_id" not in r:
                    problems.append(f"{ev}: no stim_id column")
                    break
                if r["trial_type"] == "video on":
                    rows.append((ev, i, r["stim_id"]))
                elif r["stim_id"] != "n/a":
                    problems.append(f"{ev}:{i}: stim_id {r['stim_id']!r} on a '{r['trial_type']}' row")
        c["sessions"] += 1
        c["video_on_rows"] += len(rows)
        ids = [norm(s) for _, _, s in rows]
        # 1. which ds004488 participant was shown in this order
        hits = [k for k, seq in fmri.items() if seq[: len(ids)] == ids and len(ids) > 0]
        if len(hits) != 1:
            problems.append(f"sub-{sub} ses-{ses}: {len(ids)} trials match {len(hits)} ds004488 lists {hits[:3]}")
            continue
        c["sessions_matched_one_list"] += 1
        c["sessions_complete_720"] += len(ids) == 720
        # 3. detailed_events of the same participant and session
        det = [r for r in read_tsv(f"derivatives/detailed_events/sub-{sub}_events.tsv")
               if r["session"] == ses and r["event_name"] == "video_on"]
        det.sort(key=lambda r: int(r["run"]))  # stable: keeps the within-run order
        if len(det) != len(rows):
            problems.append(f"sub-{sub} ses-{ses}: {len(rows)} 'video on' rows, {len(det)} in detailed_events")
        for k, (ev, line, sid) in enumerate(rows):
            # 2. same clip, same position
            if norm(sid) != fmri[hits[0]][k]:
                problems.append(f"{ev}:{line}: stim_id {sid} != {hits[0]} clip {fmri[hits[0]][k]}")
                continue
            # 4. in stimuli.tsv
            if sid not in stim:
                problems.append(f"{ev}:{line}: stim_id {sid} not in stimuli/stimuli.tsv")
                continue
            mm = re.match(r"v_(.+)_id_(.+)_start_[0-9.]+_label_\d+$", sid)
            pair = (norm(mm.group(1)), mm.group(2))
            if k < len(det):
                d = det[k]
                if (norm(d["class_name"]), d["video_id"]) != pair:
                    problems.append(f"{ev}:{line}: stim_id {sid} vs detailed_events {d['class_name']}/{d['video_id']}")
                    continue
            c["rows_matched"] += 1
            c["rows_resolved_only_by_order" if by_pair[pair] > 1 else "rows_also_unique_in_detailed_events"] += 1

    for k in ["events_files", "sessions", "sessions_matched_one_list", "sessions_complete_720", "video_on_rows",
              "rows_matched", "rows_also_unique_in_detailed_events", "rows_resolved_only_by_order"]:
        print(f"{k}: {c[k]}")
    print(f"rows_failed: {len(problems)}")
    for p in problems[:50]:
        print("  ", p)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
