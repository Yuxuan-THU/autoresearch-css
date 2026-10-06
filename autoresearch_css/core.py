"""Core building blocks for CSS AutoResearch MVP."""
from __future__ import annotations
import csv, json, math, statistics, hashlib, datetime
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

@dataclass
class DatasetProfile:
    path: str
    format: str
    rows: int
    columns: list[str]
    numeric_columns: list[str]
    categorical_columns: list[str]
    missingness: dict[str, float]
    warnings: list[str] = field(default_factory=list)

@dataclass
class ResearchQuestion:
    id: str
    question: str
    mechanism: str
    theory_anchor: str
    novelty_claim: str
    required_variables: list[str]
    analysis_plan: str
    feasibility: float = 0.0
    novelty: float = 0.0
    theoretical_value: float = 0.0
    empirical_signal: float = 0.0
    risk: float = 0.0
    status: str = "proposed"
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def score(self) -> float:
        return round(.25*self.feasibility + .25*self.novelty + .2*self.theoretical_value + .3*self.empirical_signal - .1*self.risk, 3)


def _read_rows(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        obj = json.loads(path.read_text(encoding="utf-8"))
        rows = obj if isinstance(obj, list) else obj.get("data", [])
    elif path.suffix.lower() in {".jsonl", ".ndjson"}:
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    else:
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def profile_dataset(path: str, sample_limit: int | None = None) -> DatasetProfile:
    p = Path(path)
    rows = _read_rows(p, sample_limit)
    columns = list(rows[0]) if rows else []
    numeric, categorical, missing = [], [], {}
    for c in columns:
        vals = [r.get(c) for r in rows]
        missing[c] = round(sum(v in (None, "", "NA", "null") for v in vals) / max(1, len(vals)), 4)
        converted = []
        for v in vals:
            try: converted.append(float(v))
            except (TypeError, ValueError): pass
        if len(converted) >= max(3, int(.8*len(vals))) and len(set(converted)) > 1:
            numeric.append(c)
        else: categorical.append(c)
    warnings = []
    if not rows: warnings.append("数据为空或格式未识别")
    if len(rows) < 100: warnings.append("样本量较小：推断结果只能作为探索性证据")
    if any(v > .2 for v in missing.values()): warnings.append("部分变量缺失率超过 20%")
    return DatasetProfile(str(p), p.suffix.lower(), len(rows), columns, numeric, categorical, missing, warnings)


def _num(rows, col):
    out=[]
    for r in rows:
        try:
            x=float(r.get(col, ""));
            if math.isfinite(x): out.append(x)
        except (TypeError, ValueError): pass
    return out


def _corr(x, y):
    n=min(len(x),len(y)); x=x[:n]; y=y[:n]
    if n<3: return None
    mx,my=statistics.mean(x),statistics.mean(y)
    dx=[a-mx for a in x]; dy=[b-my for b in y]
    den=math.sqrt(sum(a*a for a in dx)*sum(b*b for b in dy))
    return round(sum(a*b for a,b in zip(dx,dy))/den,4) if den else 0.0


def generate_questions(profile: DatasetProfile, direction: str, count: int = 10) -> list[ResearchQuestion]:
    nums = profile.numeric_columns
    cats = profile.categorical_columns
    pairs = [(a,b) for a in nums for b in nums if a < b][:count]
    qs=[]
    for i,(x,y) in enumerate(pairs or [("因变量","解释变量")]):
        group = cats[0] if cats else "群体/地区类型"
        qs.append(ResearchQuestion(
            id=f"RQ{i+1:02d}",
            question=f"在{direction}中，{x}与{y}的关系是否因{group}而异？这种异质性是否揭示一种被忽视的机制？",
            mechanism=f"{group}可能调节 {x} → {y} 的作用路径",
            theory_anchor="能力/资源约束与制度性异质性理论",
            novelty_claim="从总体平均效应转向可检验的情境化异质性机制",
            required_variables=[x,y,group],
            analysis_plan=f"比较不同 {group} 组的相关/均值差异，并报告效应量与置信区间"
        ))
    return qs[:count]


def evaluate_questions(questions, path: str):
    rows=_read_rows(Path(path))
    for q in questions:
        x,y=q.required_variables[:2]
        xv,yv=_num(rows,x),_num(rows,y)
        corr=_corr(xv,yv)
        q.feasibility=round(sum(v in (profile_dataset(path).columns) for v in q.required_variables)/len(q.required_variables),2)
        q.empirical_signal=round(min(1, abs(corr or 0)),2)
        q.novelty=.55; q.theoretical_value=.65; q.risk=.25
        q.evidence={"correlation":corr,"n_x":len(xv),"n_y":len(yv)}
        q.status="promising" if q.score >= .35 else "weak_signal"
    return sorted(questions, key=lambda x:x.score, reverse=True)


def run_mvp(path: str, direction: str, count: int=10):
    profile=profile_dataset(path)
    questions=evaluate_questions(generate_questions(profile,direction,count),path)
    return profile, questions


def build_manifest(dataset_path: str, direction: str, profile: DatasetProfile, questions: list[ResearchQuestion]):
    data = Path(dataset_path).read_bytes()
    return {
        "manifest_version": "0.1",
        "run_id": hashlib.sha256((str(datetime.datetime.now(datetime.timezone.utc)) + dataset_path).encode()).hexdigest()[:16],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "dataset": {"path": dataset_path, "sha256": hashlib.sha256(data).hexdigest()},
        "direction": direction, "rows": profile.rows, "columns": profile.columns,
        "question_count": len(questions), "status": "exploratory_shortlist",
        "limitations": ["自动生成的新颖性分数不是文献证明", "相关性不是因果性", "需要人工 scope lock"]
    }


def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=lambda o: asdict(o)), encoding="utf-8")
