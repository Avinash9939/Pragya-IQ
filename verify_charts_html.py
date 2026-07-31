def format_charts_html(rec_chart):
    charts_split = [c.strip() for c in rec_chart.split(",") if c.strip()]
    rec_chart_html = "".join([f'<span style="display: block; line-height: 1.4; margin-bottom: 2px;">{c}</span>' for c in charts_split])
    return rec_chart_html

# Test 1: Single chart
t1 = format_charts_html("Sales Trend (Line Chart)")
print("Test 1:", repr(t1))
assert t1 == '<span style="display: block; line-height: 1.4; margin-bottom: 2px;">Sales Trend (Line Chart)</span>'

# Test 2: Multiple charts
t2 = format_charts_html("Sales Trend (Line Chart), Category Performance (Bar Chart)")
print("Test 2:", repr(t2))
assert t2 == '<span style="display: block; line-height: 1.4; margin-bottom: 2px;">Sales Trend (Line Chart)</span><span style="display: block; line-height: 1.4; margin-bottom: 2px;">Category Performance (Bar Chart)</span>'

print("\nVerification Passed Successfully!")
