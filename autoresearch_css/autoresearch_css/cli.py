from __future__ import annotations
import argparse, json
from dataclasses import asdict
from .core import run_mvp, save_json, build_manifest

def main():
    ap=argparse.ArgumentParser(description='AutoResearch for Computational Social Science')
    ap.add_argument('dataset', help='CSV/JSON/JSONL dataset path')
    ap.add_argument('--direction', required=True, help='broad research direction')
    ap.add_argument('--count', type=int, default=10)
    ap.add_argument('--out', default='autoresearch_report.json')
    args=ap.parse_args()
    profile, questions=run_mvp(args.dataset,args.direction,args.count)
    report={'dataset_profile':asdict(profile),'manifest':build_manifest(args.dataset,args.direction,profile,questions),'shortlist':[asdict(q)|{'score':q.score} for q in questions]}
    save_json(args.out,report)
    print(f'Profiled {profile.rows} rows, {len(profile.columns)} columns')
    print(f'Wrote {args.out}')
    for q in questions[:3]: print(f'{q.id} score={q.score}: {q.question}')
if __name__=='__main__': main()
