#Cheap Chicago - Final project for CS122

# Carlos O. Grandet Caballero
# Hector Salvador Lopez

'''
This code acts as the views page of the Django site 
'''

from django.shortcuts import render
from django.http import HttpResponse
from django import forms
import json
import traceback
from io import StringIO
import sys
import csv
import os
from operator import and_
from functools import reduce
from scoring.scoring2 import run_score


RES_DIR = os.path.join(os.path.dirname(__file__), '..', 'res')

##################################
### Author: CSS122 PA3  ##
#We did not modify this code at all
##################################

def _valid_military_time(time):
    '''
    Check if valid military time
    '''
    return (0 <= time < 2400) and (time % 100 < 60)


def _load_column(filename, col=0):
    """Loads single column from csv file"""
    with open(filename) as f:
        col = list(zip(*csv.reader(f)))[0]
        return list(col)


def _load_res_column(filename, col=0):
    """Load column from resource directory"""
    return _load_column(os.path.join(RES_DIR, filename), col=col)


def _build_dropdown(options):
    """Converts a list to (value, caption) tuples"""
    return [(x, x) for x in options if x is not None ]

class IntegerRange(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (forms.IntegerField(),
                  forms.IntegerField())
        super(IntegerRange, self).__init__(fields=fields,
                                           *args, **kwargs)

    def compress(self, values):
        if values and (values[0] is None or values[1] is None):
            raise forms.ValidationError('Must specify both lower and upper '
                                        'bound, or leave both blank.')

        return values

class TimeRange(IntegerRange):
    def compress(self, values):
        super(TimeRange, self).compress(values)
        for v in values:
            if not _valid_military_time(v):
                raise forms.ValidationError('The value {:04} is not a valid military time.'.format(v))
        if values and (values[1] < values[0]):
            raise forms.ValidationError('Lower bound must not exceed upper bound.')
        return values

RANGE_WIDGET = forms.widgets.MultiWidget(widgets=(forms.widgets.NumberInput,
 
                                                  forms.widgets.NumberInput))
##################################
### This code was inspired on the PA3, but we did modifications
##################################

DAYS = _build_dropdown(_load_res_column('day_list.csv'))
NEIGH = _build_dropdown([None] + _load_res_column('neighborhood.csv'))
ESTABLISHMENTS = ["food","restaurants","beauty","active","arts","nightlife","shopping"]
EST = _build_dropdown([None] + _load_res_column('categories.csv'))
ATTR = _build_dropdown([None] + _load_res_column('attributes_form.csv'))


class SearchForm(forms.Form):
    
    neigh = forms.ChoiceField(label='Which neighborhood do you want to visit', choices=NEIGH, required=True)
    est = forms.MultipleChoiceField(label='What are you feeling like doing today',
                                     choices= EST,
                                     widget=forms.CheckboxSelectMultiple,
                                     required=True)
    attr_rest = forms.MultipleChoiceField(label='What type of experience',
                                     choices= ATTR,
                                     widget=forms.CheckboxSelectMultiple,
                                     required=False)
    time = TimeRange(
            label='Time (start/end)',
            help_text='e.g. 1000 and 1430 (meaning 10am-2:30pm)',
            widget=RANGE_WIDGET,
            required=False)
    days = forms.ChoiceField(label='Days',
                                     choices=DAYS,
                                     required=True)
    # show_args = forms.BooleanField(label='Show args_to_ui',
    #                                required=False)


def home(request):
    '''
    Create a home view with the form. 
    '''
    context = {}
    res = None
    if request.method == 'GET':
        # create a form instance and populate it with data from the request:
        form = SearchForm(request.GET)
        # check whether it's valid:
        if form.is_valid():
            # Convert form data to an args dictionary for find_courses
            args = {}
            if form.cleaned_data['neigh']:
                args['neigh'] = form.cleaned_data['neigh']
            if form.cleaned_data['est']:
                args['est'] = form.cleaned_data['est']
            if form.cleaned_data['attr_rest']:
                args['attr_rest'] = form.cleaned_data['attr_rest']
            time = form.cleaned_data['time']
            if time:
                args['time_start'] = time[0]
                args['time_end'] = time[1]
            days = form.cleaned_data['days']
            if days:
                args['day'] = days
            # if form.cleaned_data['show_args']:
            #     context['args'] = 'args_to_ui = ' + json.dumps(args, indent=2)

            # Generate a score given the arguments
            try:
                res = run_score(args)
            except:
                res = None
    else:
        form = SearchForm()

    if res is None:
        context['result'] = [["No results found"]]
    

    else:
        url, color_label, header, table = res
        #Add results of the scoring to the context of the website
        context['map'] = url 
        context['result'] = table
        context['columns'] = header
        context["color_label"] = color_label

    context['form'] = form
    return render(request, 'index.html', context)
