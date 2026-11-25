import tempfile
import unittest
from pathlib import Path
from pharma_news_bot.dedupe import _pick_by_section, _remove_near_duplicates, _same_story, dedupe_rank
from pharma_news_bot.classifier import CATEGORY_ORDER
from pharma_news_bot.models import NewsItem
from pharma_news_bot.storage import NewsStore


def news(title, summary='', source='Naver News'):
    return NewsItem(title=title, link='https://example.com/' + title, source=source, summary=summary)


class DedupeTests(unittest.TestCase):
    def test_award_rewrites(self):
        items = [
            news("최인영 한미약품 부사장 '국민훈장 목련장'", '글로벌 제약사와의 대형 기술수출 성과를 창출했다. 미국 FDA 허가 및 상용화에 성공한 롤론티스 개발'),
            news('최인영 한미약품 부사장 등 보건산업 발전 기여 유공자 포상', '최인영 한미약품 부사장은 혁신 신약 연구개발을 주도해 글로벌 제약사와의 기술수출 성과를 내고 항암제 롤론티스가 국내에서 개발한 항암 분야 바이오신약 중 최초로 미국 식품의약국 FDA 허가 및 상용화에 성공했다'),
            news('최인영 한미약품 부사장, 국민훈장 목련장 수훈', '글로벌 제약사와 대규모 기술수출 계약을 이끌었다. 국내 항암 분야 바이오신약 최초로 미국 식품의약국 FDA 허가 및 상용화에 성공한 롤론티스 개발'),
        ]
        self.assertEqual(len(_remove_near_duplicates(items)), 1)

    def test_cso_rewrites(self):
        left = news("제약사 'CSO 관리책임' 구체로…12월 약사법 개정안 발의 전망", '보건복지부는 제약기업에 CSO 관리 감독 책임을 부여하는 내용의 약사법 개정안을 국회와 협의 중이다. CSO 관련 워킹그룹을 구성해 세부 실행방안을 논의한다')
        right = news('제약사 CSO 관리책임 강화 논의…재위탁 검증체계 정비 과제', '관리책임 강화, CSO 의무 보고기준 동반 필요. 업계에서는 제약사 관리책임 강화에 공감하면서도 재위탁 검증체계 정비를 요구했다')
        self.assertTrue(_same_story(left, right))

    def test_distinct_events(self):
        pairs = [
            ('한미약품 비만치료제 임상 3상 승인', '종근당 비만치료제 임상 3상 승인'),
            ('한미약품 에페글레나타이드 임상 3상 승인', '한미약품 롤론티스 FDA 품목허가 승인'),
            ('한미약품 신약 임상 2상 결과 발표', '한미약품 신약 임상 3상 결과 발표'),
            ('', ''),
        ]
        for left, right in pairs:
            with self.subTest(left=left):
                self.assertFalse(_same_story(news(left), news(right)))

    def test_round_robin_and_cap(self):
        items = [NewsItem(title=f'{cat}-{i}', link=f'{cat}/{i}', source='test', category=cat) for cat in CATEGORY_ORDER for i in range(6)]
        self.assertEqual([item.category for item in _pick_by_section(items, 4)], CATEGORY_ORDER)
        self.assertEqual(len(_pick_by_section(items, 20)), 12)
        self.assertEqual(len(_pick_by_section(items, 0)), 0)
        self.assertEqual(len(_pick_by_section(items[:6], 12)), 3)

    def test_pipeline_selection_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NewsStore(Path(directory) / 'sent.db')
            store.init()
            items = [news('최인영 한미약품 부사장 국민훈장 목련장 수훈'), news('최인영 한미약품 부사장 국민훈장 목련장 수훈 소식', source='DailyPharm'), news('CSO 수수료 지급기준 개편')]
            result = dedupe_rank(items, store, 12, 8, True, 7)
            self.assertEqual(len(result), 2)
            self.assertIn(items[1], result)
            self.assertNotIn(items[0], result)
            store.mark_sent(result)
            self.assertEqual(dedupe_rank(result, store, 12, 8, True, 7), [])

if __name__ == '__main__':
    unittest.main()
