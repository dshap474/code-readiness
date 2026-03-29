from code_readiness_template.app import healthcheck
from code_readiness_template.features.widgets import (
    Widget,
    build_widget_slug,
    create_widget,
    get_widget,
    list_widgets,
    slugify_widget_name,
)

healthcheck()
slugify_widget_name("")
build_widget_slug("")
_ = (
    Widget,
    create_widget,
    list_widgets,
    get_widget,
)
