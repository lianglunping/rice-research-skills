#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PrimerConstraints:
    primer_min: int
    primer_max: int
    tm_min: float
    tm_max: float
    gc_min: float
    gc_max: float
    gc_target: float
    tm_target: float
    product_min: int
    product_max: int
    var_dist_min: int
    max_repeat: int
    tm_diff_max: float
    len_diff_max: int

    @classmethod
    def strict(cls) -> "PrimerConstraints":
        return cls(
            primer_min=18,
            primer_max=22,
            tm_min=57.0,
            tm_max=60.0,
            gc_min=45.0,
            gc_max=65.0,
            gc_target=55.0,
            tm_target=58.5,
            product_min=300,
            product_max=600,
            var_dist_min=100,
            max_repeat=3,
            tm_diff_max=1.0,
            len_diff_max=2,
        )

    @classmethod
    def relaxed(cls) -> "PrimerConstraints":
        return cls(
            primer_min=18,
            primer_max=24,
            tm_min=54.0,
            tm_max=62.0,
            gc_min=35.0,
            gc_max=70.0,
            gc_target=52.0,
            tm_target=58.0,
            product_min=250,
            product_max=650,
            var_dist_min=80,
            max_repeat=3,
            tm_diff_max=1.5,
            len_diff_max=3,
        )


@dataclass(frozen=True)
class VariantRecord:
    name: str
    chrom: str
    pos: int
    ref: str
    alt: str
    full_seq: str
    left_flank_len: int
    variant_type: str = "InDel"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidatePrimer:
    seq: str
    start: int
    end: int
    length: int
    gc: float
    tm: float
    dist_to_var: int
    has_gc_clamp: bool


class PrimerDesigner:
    def __init__(self, constraints: PrimerConstraints):
        self.constraints = constraints

    @staticmethod
    def calc_gc(seq: str) -> float:
        seq = seq.upper()
        gc = seq.count("G") + seq.count("C")
        return gc / len(seq) * 100 if seq else 0.0

    @staticmethod
    def calc_tm(seq: str) -> float:
        seq = seq.upper()
        gc = seq.count("G") + seq.count("C")
        length = len(seq)
        if length == 0:
            return 0.0
        return 64.9 + 41 * (gc - 16.4) / length

    @staticmethod
    def has_repeat(seq: str, max_repeat: int = 3) -> bool:
        seq = seq.upper()
        for base in "ATCG":
            if base * max_repeat in seq:
                return True
        return False

    @staticmethod
    def reverse_complement(seq: str) -> str:
        complement = str.maketrans("ATCGNatcgn", "TAGCNtagcn")
        return seq.translate(complement)[::-1].upper()

    @staticmethod
    def has_gc_clamp(seq: str) -> bool:
        return bool(seq) and seq[-1].upper() in {"G", "C"}

    def _find_forward_primers(self, full_seq: str, variant_pos: int) -> list[CandidatePrimer]:
        candidates: list[CandidatePrimer] = []
        search_end = variant_pos - self.constraints.var_dist_min
        search_start = max(0, variant_pos - self.constraints.product_max)

        for start in range(search_start, max(search_end, search_start)):
            for length in range(self.constraints.primer_min, self.constraints.primer_max + 1):
                end = start + length
                if end > len(full_seq):
                    continue
                primer = full_seq[start:end].upper()
                gc = self.calc_gc(primer)
                tm = self.calc_tm(primer)
                dist_to_var = variant_pos - end
                if (
                    self.constraints.gc_min <= gc <= self.constraints.gc_max
                    and self.constraints.tm_min <= tm <= self.constraints.tm_max
                    and not self.has_repeat(primer, self.constraints.max_repeat)
                    and dist_to_var >= self.constraints.var_dist_min
                ):
                    candidates.append(
                        CandidatePrimer(
                            seq=primer,
                            start=start,
                            end=end,
                            length=length,
                            gc=gc,
                            tm=tm,
                            dist_to_var=dist_to_var,
                            has_gc_clamp=self.has_gc_clamp(primer),
                        )
                    )
        return candidates

    def _find_reverse_primers(self, full_seq: str, variant_pos: int, ref_len: int) -> list[CandidatePrimer]:
        candidates: list[CandidatePrimer] = []
        var_end = variant_pos + ref_len
        search_start = var_end + self.constraints.var_dist_min
        search_end = min(len(full_seq), variant_pos + self.constraints.product_max)

        for end in range(search_start + self.constraints.primer_min, search_end + 1):
            for length in range(self.constraints.primer_min, self.constraints.primer_max + 1):
                start = end - length
                if start < 0:
                    continue
                template = full_seq[start:end].upper()
                primer = self.reverse_complement(template)
                gc = self.calc_gc(primer)
                tm = self.calc_tm(primer)
                dist_to_var = start - var_end
                if (
                    self.constraints.gc_min <= gc <= self.constraints.gc_max
                    and self.constraints.tm_min <= tm <= self.constraints.tm_max
                    and not self.has_repeat(primer, self.constraints.max_repeat)
                    and dist_to_var >= self.constraints.var_dist_min
                ):
                    candidates.append(
                        CandidatePrimer(
                            seq=primer,
                            start=start,
                            end=end,
                            length=length,
                            gc=gc,
                            tm=tm,
                            dist_to_var=dist_to_var,
                            has_gc_clamp=self.has_gc_clamp(primer),
                        )
                    )
        return candidates

    def _pair_primers(
        self,
        forward_list: list[CandidatePrimer],
        reverse_list: list[CandidatePrimer],
        variant_pos: int,
    ) -> list[dict[str, Any]]:
        pairs: list[dict[str, Any]] = []

        for forward in forward_list:
            for reverse in reverse_list:
                tm_diff = abs(forward.tm - reverse.tm)
                len_diff = abs(forward.length - reverse.length)
                product_size = reverse.end - forward.start
                if (
                    tm_diff <= self.constraints.tm_diff_max
                    and len_diff <= self.constraints.len_diff_max
                    and self.constraints.product_min <= product_size <= self.constraints.product_max
                ):
                    var_pos_in_product = forward.dist_to_var + forward.length
                    center_ratio = var_pos_in_product / product_size
                    avg_tm = (forward.tm + reverse.tm) / 2
                    avg_gc = (forward.gc + reverse.gc) / 2
                    score = (
                        tm_diff * 3
                        + abs(avg_tm - self.constraints.tm_target)
                        + abs(avg_gc - self.constraints.gc_target) * 0.3
                        + abs(center_ratio - 0.5) * 5
                        + (0 if forward.has_gc_clamp else 1)
                        + (0 if reverse.has_gc_clamp else 1)
                    )
                    pairs.append(
                        {
                            "forward": forward,
                            "reverse": reverse,
                            "tm_diff": tm_diff,
                            "len_diff": len_diff,
                            "product_size": product_size,
                            "avg_tm": avg_tm,
                            "avg_gc": avg_gc,
                            "center_ratio": center_ratio,
                            "score": score,
                        }
                    )

        pairs.sort(key=lambda item: item["score"])
        return pairs

    def design_variant(self, record: VariantRecord, design_label: str) -> dict[str, Any]:
        ref = record.ref.upper()
        alt = record.alt.upper()
        full_seq = record.full_seq.upper()
        variant_pos = int(record.left_flank_len)
        ref_len = len(ref)

        if variant_pos < 0 or variant_pos + ref_len > len(full_seq):
            return {
                "name": record.name,
                "status": "FAILED",
                "reason": "invalid_variant_window",
                "design_params": design_label,
            }

        observed_ref = full_seq[variant_pos : variant_pos + ref_len]
        if observed_ref != ref:
            return {
                "name": record.name,
                "status": "FAILED",
                "reason": "full_seq_ref_mismatch",
                "design_params": design_label,
            }

        forward_candidates = self._find_forward_primers(full_seq, variant_pos)
        if not forward_candidates:
            return {
                "name": record.name,
                "status": "FAILED",
                "reason": "no_forward_primer",
                "design_params": design_label,
            }

        reverse_candidates = self._find_reverse_primers(full_seq, variant_pos, ref_len)
        if not reverse_candidates:
            return {
                "name": record.name,
                "status": "FAILED",
                "reason": "no_reverse_primer",
                "design_params": design_label,
            }

        pairs = self._pair_primers(forward_candidates, reverse_candidates, variant_pos)
        if not pairs:
            return {
                "name": record.name,
                "status": "FAILED",
                "reason": "no_primer_pair",
                "design_params": design_label,
            }

        best = pairs[0]
        forward = best["forward"]
        reverse = best["reverse"]
        indel_size = len(ref) - len(alt)
        wt_size = best["product_size"]
        mt_size = wt_size - indel_size

        return {
            "name": record.name,
            "status": "SUCCESS",
            "reason": "",
            "chrom": record.chrom,
            "pos": record.pos,
            "ref": ref,
            "alt": alt,
            "variant_type": record.variant_type,
            "indel_size": indel_size,
            "forward_name": f"{record.name}-F",
            "forward_seq": forward.seq,
            "forward_len": forward.length,
            "forward_tm": round(forward.tm, 1),
            "forward_gc": round(forward.gc, 1),
            "reverse_name": f"{record.name}-R",
            "reverse_seq": reverse.seq,
            "reverse_len": reverse.length,
            "reverse_tm": round(reverse.tm, 1),
            "reverse_gc": round(reverse.gc, 1),
            "product_wt": wt_size,
            "product_mt": mt_size,
            "tm_diff": round(best["tm_diff"], 2),
            "avg_tm": round(best["avg_tm"], 1),
            "avg_gc": round(best["avg_gc"], 1),
            "var_dist_f": forward.dist_to_var,
            "var_dist_r": reverse.dist_to_var,
            "center_ratio": round(best["center_ratio"] * 100, 1),
            "score": round(best["score"], 2),
            "design_params": design_label,
        }


def design_batch(records: list[VariantRecord], constraints: PrimerConstraints, design_label: str) -> list[dict[str, Any]]:
    designer = PrimerDesigner(constraints)
    return [designer.design_variant(record, design_label) for record in records]
