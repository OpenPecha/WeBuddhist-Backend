"""add tradition code/description and seed catalog

Revision ID: tr1a2b3c4d5e
Revises: b4d7e9f1a2c3
Create Date: 2026-08-10 12:00:00.000000

Adds ``tradition_list.code`` and ``tradition_metadata.description``, then seeds
the supported traditions (pali, chinese, tibetan) and localized metadata rows
so list/get endpoints can read from the database without tradition.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import UUID, uuid4, uuid5

import sqlalchemy as sa
from alembic import op

from migrations.idempotency import column_exists, index_exists, table_exists

revision: str = "tr1a2b3c4d5e"
down_revision: Union[str, None] = "b4d7e9f1a2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TRADITION_ID_NAMESPACE = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")

TRADITIONS = (
    {
        "code": "pali",
        "regions": [
            "Sri Lanka",
            "Thailand",
            "Myanmar",
            "Cambodia",
            "Laos",
            "Bangladesh",
            "India",
        ],
    },
    {
        "code": "chinese",
        "regions": ["China", "Korea", "Japan", "Vietnam"],
    },
    {
        "code": "tibetan",
        "regions": ["Tibet", "India", "Nepal", "Bhutan", "Mongolia", "Russia"],
    },
)

METADATA_BY_CODE = {
    "pali": {
        "EN": (
            "Pāli scriptures",
            "Followed across Sri Lanka, Thailand, Myanmar, Cambodia, Laos, and Bangladesh, and in central and western India.",
        ),
        "HI": (
            "पालि ग्रंथ",
            "श्रीलंका, थाईलैंड, म्यांमार, कंबोडिया, लाओस, बांग्लादेश और मध्य व पश्चिमी भारत में इसका अनुसरण किया जाता है।",
        ),
        "BO": (
            "པ་ལིའི་བཀའ་བསྟན།",
            "ཤྲཱི་ལངྐ་དང་། ཐཱ་ལེནྜ། འབར་མ། ཀམ་བྷོ་ཌི་ཡ། ལའོ་སུ། བྷངྒ་ལ་དེ་ཤ། དེ་བཞིན་རྒྱ་གར་དབུས་རྒྱུད་དང་ནུབ་རྒྱུད་བཅས་སུ་ཉམས་ལེན་བྱེད།",
        ),
        "MN": (
            "Пали судар бичиг",
            "Шри-Ланка, Тайланд, Мьянмар, Камбож, Лаос, Бангладеш болон Энэтхэгийн төв, баруун бүс нутагт дагаж мөрддөг.",
        ),
        "NE": (
            "पालि ग्रन्थ",
            "श्रीलंका, थाइल्याण्ड, म्यानमार, कम्बोडिया, लाओस, बंगलादेश र मध्य तथा पश्चिमी भारतमा अनुसरण गरिन्छ।",
        ),
        "ZH": (
            "巴利语经典",
            "盛行于斯里兰卡、泰国、缅甸、柬埔寨、老挝、孟加拉国以及印度中部和西部地区。",
        ),
    },
    "chinese": {
        "EN": (
            "Chinese scriptures",
            "Followed across China, Korea, Japan, and Vietnam.",
        ),
        "HI": (
            "चीनी ग्रंथ",
            "चीन, कोरिया, जापान और वियतनाम में इसका अनुसरण किया जाता है।",
        ),
        "BO": (
            "རྒྱ་ཡིག་བཀའ་བསྟན།",
            "རྒྱ་ནག་དང་། ཀོ་རི་ཡ། ཉི་ཧོང་། ཝི་ཏི་ནམ་བཅས་སུ་ཉམས་ལེན་བྱེད།",
        ),
        "MN": (
            "Хятад судар бичиг",
            "Хятад, Солонгос, Япон, Вьетнам улсуудад дагаж мөрддөг.",
        ),
        "NE": (
            "चिनियाँ ग्रन्थ",
            "चीन, कोरिया, जापान र भियतनाममा अनुसरण गरिन्छ।",
        ),
        "ZH": (
            "汉语经典",
            "盛行于中国、韩国、日本和越南。",
        ),
    },
    "tibetan": {
        "EN": (
            "Sanskrit & Tibetan scriptures",
            "Followed across the Tibetan plateau and the Himalayan regions of India, Nepal, and Bhutan, as well as Mongolia and Russia.",
        ),
        "HI": (
            "संस्कृत और तिब्बती ग्रंथ",
            "तिब्बती पठार और भारत, नेपाल व भूटान के हिमालयी क्षेत्रों के साथ-साथ मंगोलिया और रूस में इसका अनुसरण किया जाता है।",
        ),
        "BO": (
            "ལེགས་སྦྱར་དང་བོད་ཡིག་བཀའ་བསྟན།",
            "བོད་མཐོ་སྒང་དང་། རྒྱ་གར་དང་བལ་ཡུལ་གྱི་ཧི་མ་ལ་ཡའི་ས་ཁུལ། འབྲུག་ཡུལ། དེ་བཞིན་སོག་ཡུལ་དང་ཨུ་རུ་སུ་བཅས་སུ་ཉམས་ལེན་བྱེད།",
        ),
        "MN": (
            "Санскрит ба Төвөд судар бичиг",
            "Төвөдийн өндөрлөг болон Энэтхэг, Непал, Бутаны Гималайн бүс нутаг, түүнчлэн Монгол, Орос улсуудад дагаж мөрддөг.",
        ),
        "NE": (
            "संस्कृत र तिब्बती ग्रन्थ",
            "तिब्बती पठार र भारत, नेपाल तथा भुटानका हिमाली क्षेत्रहरूका साथै मङ्गोलिया र रुसमा अनुसरण गरिन्छ।",
        ),
        "ZH": (
            "梵语与藏语经典",
            "盛行于青藏高原、印度喜马拉雅地区、尼泊尔、不丹，以及蒙古和俄罗斯。",
        ),
    },
}


def _tradition_id(code: str) -> UUID:
    return uuid5(TRADITION_ID_NAMESPACE, code)


def upgrade() -> None:
    if not table_exists("tradition_list") or not table_exists("tradition_metadata"):
        return

    if not column_exists("tradition_list", "code"):
        op.add_column("tradition_list", sa.Column("code", sa.String(length=64), nullable=True))

    if not column_exists("tradition_metadata", "description"):
        op.add_column("tradition_metadata", sa.Column("description", sa.Text(), nullable=True))

    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    for tradition in TRADITIONS:
        code = tradition["code"]
        tradition_id = _tradition_id(code)
        regions_json = json.dumps(tradition["regions"])

        existing = conn.execute(
            sa.text("SELECT id, code FROM tradition_list WHERE id = :id OR code = :code"),
            {"id": str(tradition_id), "code": code},
        ).mappings().first()

        if existing is None:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO tradition_list (id, code, parent_id, regions, created_at, updated_at)
                    VALUES (:id, :code, NULL, CAST(:regions AS jsonb), :created_at, :updated_at)
                    """
                ),
                {
                    "id": str(tradition_id),
                    "code": code,
                    "regions": regions_json,
                    "created_at": now,
                    "updated_at": now,
                },
            )
        else:
            conn.execute(
                sa.text(
                    """
                    UPDATE tradition_list
                    SET code = :code,
                        regions = CAST(:regions AS jsonb),
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": str(existing["id"]),
                    "code": code,
                    "regions": regions_json,
                    "updated_at": now,
                },
            )
            tradition_id = existing["id"]

        for language, (name, description) in METADATA_BY_CODE[code].items():
            existing_meta = conn.execute(
                sa.text(
                    """
                    SELECT id FROM tradition_metadata
                    WHERE tradition_id = :tradition_id AND language = CAST(:language AS languagecode)
                    """
                ),
                {"tradition_id": str(tradition_id), "language": language},
            ).first()

            if existing_meta is None:
                conn.execute(
                    sa.text(
                        """
                        INSERT INTO tradition_metadata
                            (id, tradition_id, language, name, description, other_names, created_at, updated_at)
                        VALUES
                            (
                                :id,
                                :tradition_id,
                                CAST(:language AS languagecode),
                                :name,
                                :description,
                                NULL,
                                :created_at,
                                :updated_at
                            )
                        """
                    ),
                    {
                        "id": str(uuid4()),
                        "tradition_id": str(tradition_id),
                        "language": language,
                        "name": name,
                        "description": description,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
            else:
                conn.execute(
                    sa.text(
                        """
                        UPDATE tradition_metadata
                        SET name = :name,
                            description = :description,
                            updated_at = :updated_at
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": str(existing_meta[0]),
                        "name": name,
                        "description": description,
                        "updated_at": now,
                    },
                )

    conn.execute(
        sa.text(
            """
            UPDATE tradition_list
            SET code = 'legacy_' || REPLACE(id::text, '-', '')
            WHERE code IS NULL
            """
        )
    )

    op.alter_column("tradition_list", "code", existing_type=sa.String(length=64), nullable=False)

    if not index_exists("tradition_list", "uq_tradition_list_code"):
        op.create_index("uq_tradition_list_code", "tradition_list", ["code"], unique=True)


def downgrade() -> None:
    if not table_exists("tradition_list"):
        return

    if index_exists("tradition_list", "uq_tradition_list_code"):
        op.drop_index("uq_tradition_list_code", table_name="tradition_list")

    if column_exists("tradition_metadata", "description"):
        op.drop_column("tradition_metadata", "description")

    if column_exists("tradition_list", "code"):
        op.drop_column("tradition_list", "code")
