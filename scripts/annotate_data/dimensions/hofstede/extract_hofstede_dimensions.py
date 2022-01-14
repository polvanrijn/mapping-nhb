import json
import pandas as pd

# data scraped from https://www.hofstede-insights.com/country-comparison/
with open('hofstede-insights.json') as json_file:
    data = json.load(json_file)

pd.DataFrame({
    'individualism_collectivism': [d['idv'] for d in data],
    'uncertainty_avoidance': [d['uai'] for d in data],
    'power_distance': [d['pdi'] for d in data],
    'masculinity_femininity': [d['mas'] for d in data],
    'lt_st_orientation': [d['lto'] for d in data],
    'indulgence_restraint': [d['ivr'] for d in data],
    'country': [d['title'] for d in data]
}).to_csv('hofstede-insights.csv')
