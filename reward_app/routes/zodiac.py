from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import random
import zlib
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from reward_app.database.async_db import get_async_session
from reward_app.core.config import make_resp

router = APIRouter()

ZODIACS = ['쥐','소','호랑이','토끼','용','뱀','말','양','원숭이','닭','개','돼지']


def php_weekday_today(d: Optional[date] = None) -> int:
    """
    PHP date('w') 기준: 일=0 ... 토=6
    MySQL: DAYOFWEEK(CURDATE())-1 도 동일하게 일=0 ... 토=6
    """
    d = d or date.today()
    # Python weekday(): 월=0..일=6 -> PHP식으로 변환
    return (d.weekday() + 1) % 7


@dataclass
class HoroscopeGenerator:
    db: AsyncSession

    def zodiac_by_year(self, year: int) -> str:
        mapping = ['원숭이','닭','개','돼지','쥐','소','호랑이','토끼','용','뱀','말','양']
        return mapping[year % 12]

    def tone_by(self, zodiac: str, weekday: int) -> str:
        by_weekday = {
            0: 'calm',    # 일
            1: 'focus',   # 월
            2: 'social',  # 화
            3: 'focus',   # 수
            4: 'money',   # 목
            5: 'social',  # 금
            6: 'active',  # 토
        }
        base = by_weekday.get(weekday, 'neutral')

        zodiac_tone = {
            '쥐': 'focus',
            '소': 'calm',
            '호랑이': 'active',
            '토끼': 'social',
            '용': 'active',
            '뱀': 'focus',
            '말': 'active',
            '양': 'social',
            '원숭이': 'social',
            '닭': 'focus',
            '개': 'calm',
            '돼지': 'calm',
        }
        z_tone = zodiac_tone.get(zodiac, 'neutral')

        override_pairs = {
            'money|active': 'active',
            'money|social': 'social',
            'money|focus':  'focus',
            'focus|active': 'active',
            'social|focus': 'focus',
            'active|calm':  'calm',
        }

        return override_pairs.get(f"{base}|{z_tone}", base)

    async def generate(self, zodiac: str, weekday: int, date_ymd: Optional[str] = None) -> Dict[str, Any]:
        date_ymd = date_ymd or date.today().strftime("%Y-%m-%d")
        tone = self.tone_by(zodiac, weekday)

        # PHP: crc32(date|zodiac|weekday) 기반 고정 시드
        seed_bytes = f"{date_ymd}|{zodiac}|{weekday}".encode("utf-8")
        seed = zlib.crc32(seed_bytes) & 0xffffffff
        rng = random.Random(seed)

        opening  = await self.pick("opening",  tone="neutral", rng=rng)
        advice   = await self.pick("advice",   tone="neutral", rng=rng)
        money    = await self.pick("money",    tone="money",   rng=rng)
        relation = await self.pick("relation", tone="social",  rng=rng)
        caution  = await self.pick("caution",  tone="caution", rng=rng)
        lucky    = await self.pick("lucky",    tone="lucky",   rng=rng)

        extra = await self.pick("advice", tone="neutral", bias_tone=tone, rng=rng)

        parts = [
            opening,
            f"조언: {advice}" if advice else "",
            f"한 줄 더: {extra}" if extra else "",
            f"금전: {money}" if money else "",
            f"관계: {relation}" if relation else "",
            f"주의: {caution}" if caution else "",
            lucky,
        ]
        text_out = "\n".join([p for p in parts if p])

        return {
            "zodiac": zodiac,
            "weekday": weekday,
            "tone": tone,
            "fortune": text_out,   # 기존 응답 키가 fortune이면 유지
            "date": date_ymd,
        }

    async def pick(
        self,
        part_type: str,
        tone: Optional[str] = None,
        bias_tone: Optional[str] = None,
        rng: Optional[random.Random] = None,
    ) -> str:
        """
        PHP pick() 변환:
        - part_type 필터
        - tone 지정 시: (tone = :tone OR tone IS NULL)
        - bias_tone과 row.tone이 같으면 weight*1.3
        - weight 1~50 clamp
        - 가중치 랜덤
        """
        rng = rng or random.Random()

        # ✅ 여기 SQL만 실제 테이블/컬럼명에 맞게 수정하면 됩니다.
        if tone is None:
            sql = text("""
                SELECT text, weight, tone
                FROM horoscope_parts
                WHERE part_type = :part_type
            """)
            params = {"part_type": part_type}
        else:
            sql = text("""
                SELECT text, weight, tone
                FROM horoscope_parts
                WHERE part_type = :part_type
                  AND (tone = :tone OR tone IS NULL)
            """)
            params = {"part_type": part_type, "tone": tone}

        res = await self.db.execute(sql, params)
        rows = res.mappings().all()
        if not rows:
            return ""

        candidates: List[str] = []
        weights: List[int] = []

        for r in rows:
            w = int(r.get("weight") or 10)
            if bias_tone and (r.get("tone") == bias_tone):
                w = int(round(w * 1.3))
            w = max(1, min(w, 50))

            candidates.append(r["text"])
            weights.append(w)

        return rng.choices(candidates, weights=weights, k=1)[0]


@router.post("/list", name="운세", description="")
async def unse(db: AsyncSession = Depends(get_async_session)):
    # 기존 SQL의 DAYOFWEEK(CURDATE())-1 과 동일한 값
    weekday = php_weekday_today()

    gen = HoroscopeGenerator(db=db)

    results: Dict[str, Any] = {}
    for zodiac in ZODIACS:
        results[zodiac] = await gen.generate(zodiac=zodiac, weekday=weekday)

    # 기존 응답 구조처럼 list 형태를 원하면 변환
    list_out = [
        {
            "zodiac": z,
            "fortune": results[z]["fortune"],
            "tone": results[z]["tone"],
            "weekday": results[z]["weekday"],
            "date": results[z]["date"],
        }
        for z in ZODIACS
    ]

    return make_resp("S", {"weekday": weekday, "list": list_out})
