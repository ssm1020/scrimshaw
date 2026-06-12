import streamlit as st
import altair as alt
#### Line chart with crosshair and tooltip
def crosshair_line_chart(df, x_field, y_field, x_title, y_title, y_format, color="#00e5a0", height=300):
    ### LAYERS ###
    nearest = alt.selection_point(
        nearest=True, on="mouseover", fields=[x_field], empty=False
    )

    line = alt.Chart(df).mark_line(color=color).encode(
        x=alt.X(f"{x_field}:T", title=x_title),
        y=alt.Y(f"{y_field}:Q", title=y_title, axis=alt.Axis(format=y_format))
    )

    selectors = alt.Chart(df).mark_point().encode(
        x=f"{x_field}:T",
        opacity=alt.value(0),
        tooltip=[
            alt.Tooltip(f"{x_field}:T", title=x_title),
            alt.Tooltip(f"{y_field}:Q", title=y_title, format=y_format)
        ]
    ).add_params(nearest)

    rule = alt.Chart(df).mark_rule(color="gray").encode(
        x=f"{x_field}:T",
        opacity=alt.condition(nearest, alt.value(0.5), alt.value(0))
    ).transform_filter(nearest)

    point = line.mark_point(color=color, size=60).encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    ).transform_filter(nearest)

    return alt.layer(line, selectors, rule, point).properties(height=height)

#### Bar chart with crosshair and tooltip
def crosshair_bar_chart(df, x_field, y_field, x_title, y_title, y_format, color="#00e5a0", height=300, sort=None):
    nearest = alt.selection_point(
        nearest=True, on="mouseover", fields=[x_field], empty=False
    )

    x_enc = alt.X(f"{x_field}:N", title=x_title, sort=sort)

    bar = alt.Chart(df).mark_bar(color=color).encode(
        x=x_enc,
        y=alt.Y(f"{y_field}:Q", title=y_title, axis=alt.Axis(format=y_format))
    )

    selectors = alt.Chart(df).mark_point().encode(
        x=x_enc,
        opacity=alt.value(0),
        tooltip=[
            alt.Tooltip(f"{x_field}:N", title=x_title),
            alt.Tooltip(f"{y_field}:Q", title=y_title, format=y_format)
        ]
    ).add_params(nearest)

    rule = alt.Chart(df).mark_rule(color="gray").encode(
        x=x_enc,
        opacity=alt.condition(nearest, alt.value(0.5), alt.value(0))
    ).transform_filter(nearest)

    highlight = bar.encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0.85))
    )

    return alt.layer(highlight, selectors, rule).properties(height=height)