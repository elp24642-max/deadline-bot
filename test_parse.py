import unittest
from datetime import datetime

from parse import TZ, format_left, parse_add

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=TZ)


class ParseAddTest(unittest.TestCase):
    def test_date_and_time(self):
        title, due = parse_add("25.11 18:00 Лабораторная по C", NOW)
        self.assertEqual(title, "Лабораторная по C")
        self.assertEqual(due, datetime(2026, 11, 25, 18, 0, tzinfo=TZ))

    def test_default_time_is_end_of_day(self):
        _, due = parse_add("25.11 Отчёт", NOW)
        self.assertEqual((due.hour, due.minute), (23, 59))

    def test_explicit_year(self):
        _, due = parse_add("01.02.2027 Экзамен", NOW)
        self.assertEqual(due.year, 2027)

    def test_past_date_without_year_goes_to_next_year(self):
        _, due = parse_add("01.09 Начало семестра", NOW)
        self.assertEqual(due.year, 2027)

    def test_title_with_digits_is_not_time(self):
        title, due = parse_add("25.11 3 задачи по Python", NOW)
        self.assertEqual(title, "3 задачи по Python")
        self.assertEqual(due.hour, 23)

    def test_bad_input(self):
        for text in ["", "Лабораторная", "25.11", "31.02 Тест", "25.11 25:99 Тест"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_add(text, NOW)


class FormatLeftTest(unittest.TestCase):
    def test_values(self):
        self.assertEqual(format_left(-5), "просрочено")
        self.assertEqual(format_left(45 * 60), "45 мин")
        self.assertEqual(format_left(3 * 3600 + 120), "3 ч 2 мин")
        self.assertEqual(format_left(2 * 86400 + 5 * 3600), "2 д 5 ч")


if __name__ == "__main__":
    unittest.main()
