from database import Database
db = Database('database.db')

all_activities = db.get_all_activities(limit=100000)

# Group by category and subtype (same logic as endpoint)
activity_types = {}
for act in all_activities:
    try:
        a = dict(act) if not isinstance(act, dict) else act
        category = a.get('category', 'Unknown')
        subtype = a.get('subtype', 'Unknown')
        eco_score = float(a.get('eco_score') or 0)
        
        key = f'{category}::{subtype}'
        if key not in activity_types:
            activity_types[key] = {
                'category': category,
                'subtype': subtype,
                'eco_scores': [],
                'count': 0
            }
        
        activity_types[key]['eco_scores'].append(eco_score)
        activity_types[key]['count'] += 1
    except Exception as e:
        print(f'Error processing activity: {e}')
        continue

print(f'Activity types found: {len(activity_types)}')
for key, data in activity_types.items():
    print(f'{key}: count={data["count"]}, eco_scores={data["eco_scores"]}')

# Now test the stats calculation
result = []
for key, data in activity_types.items():
    eco_scores = data['eco_scores']
    avg_eco = sum(eco_scores) / len(eco_scores) if eco_scores else 0
    min_eco = min(eco_scores) if eco_scores else 0
    max_eco = max(eco_scores) if eco_scores else 0
    
    result.append({
        'category': data['category'],
        'subtype': data['subtype'],
        'count': data['count'],
        'avg_eco_score': round(avg_eco, 3),
        'min_eco_score': round(min_eco, 2),
        'max_eco_score': round(max_eco, 2)
    })

print(f'\nFinal result for API:')
import json
print(json.dumps(result, indent=2))
