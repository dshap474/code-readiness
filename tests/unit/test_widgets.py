from code_readiness_template.features.widgets import build_widget_slug, slugify_widget_name


def test_slugify_widget_name_normalizes_case_and_spacing() -> None:
    assert slugify_widget_name("  Fancy Widget Name  ") == "fancy-widget-name"


def test_slugify_widget_name_falls_back_for_empty_slug() -> None:
    assert build_widget_slug("!!!") == "widget"
