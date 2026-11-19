"""Prevent distorted compositions: correct offsets, aligned categories, full totals."""
import unittest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datenfutter.charts import render_chart

THEME={'cream':'#FAF8EF','navy':'#1C2D57','muted':'#626C80','grid':'#DDDCD3','dpi':120,'language':'de'}

class StackedBarsTests(unittest.TestCase):
    def test_label_wider_than_its_segment_remains_readable_outside_the_bar(self):
        # A narrow component must not print white digits across adjacent fills.
        chart={'type':'bar','stacked':True,'orientation':'horizontal',
               'y_limits':[0,2.3],'decimals':2}
        series=[{'id':str(i),'label':str(i),'color':color,'rows':[('Example',value)]}
                for i,(value,color) in enumerate([(1.8,'#1C2D57'),(.08,'#A85736'),(.32,'#526B73')])]
        render_chart(self.ax,chart,series,THEME)
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        label=next(t for t in self.ax.texts if t.get_text()=='0,08')
        box=label.get_window_extent(renderer)
        self.assertFalse(any(box.overlaps(p.get_window_extent(renderer)) for p in self.ax.patches))
        self.assertNotEqual(label.get_color(),'#FFFFFF')
        self.assertEqual([round(p.get_width(),2) for p in self.ax.patches],[1.8,.08,.32])

    def setUp(self):
        self.fig,self.ax=plt.subplots()
        self.addCleanup(plt.close,self.fig)
        self.chart={'type':'bar','stacked':True,'orientation':'horizontal','y_limits':[0,100],'expected_total':100}
        self.series=[{'id':'a','label':'A','color':'#1C2D57','rows':[('First',40),('Second',75)]},
                     {'id':'b','label':'B','color':'#A85736','rows':[('Second',25),('First',60)]}]

    def test_components_share_a_row_and_start_after_the_previous_component(self):
        result=render_chart(self.ax,self.chart,self.series,THEME)
        self.assertEqual([p.get_x() for p in self.ax.patches],[0,0,40,75])
        self.assertEqual([p.get_width() for p in self.ax.patches],[40,75,60,25])
        self.assertEqual(result['totals'],[100,100])
        self.assertEqual(result['series'][1]['values'],[60,25])
        self.assertEqual(self.ax.patches[0].get_y(),self.ax.patches[2].get_y())

    def test_missing_component_is_rejected_instead_of_implying_zero(self):
        self.series[1]['rows']=[('First',60)]
        with self.assertRaises(ValueError):render_chart(self.ax,self.chart,self.series,THEME)
        self.assertEqual(len(self.ax.patches),0)

    def test_scale_and_expected_total_check_the_sum_not_only_individual_values(self):
        for change in [{'y_limits':[0,80]},{'expected_total':90}]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                render_chart(self.ax,{**self.chart,**change},self.series,THEME)
        self.assertEqual(len(self.ax.patches),0)

    def test_zero_is_allowed_but_negative_composition_is_rejected(self):
        self.series[0]['rows']=[('First',0),('Second',75)]
        self.series[1]['rows']=[('First',100),('Second',25)]
        result=render_chart(self.ax,self.chart,self.series,THEME)
        self.assertEqual(result['totals'],[100,100])
        self.ax.clear()
        self.series[0]['rows'][0]=('First',-1)
        with self.assertRaises(ValueError):render_chart(self.ax,self.chart,self.series,THEME)
        self.assertEqual(len(self.ax.patches),0)
