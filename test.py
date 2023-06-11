import requests
import shutil
import os
from multiprocessing import Pool

def fetch_image(image_id, filename=None):
    try:
        if filename and os.path.exists(filename):
            print(f"Skipped downloading {filename}")
            return
        image_data = requests.get(url=f"https://collections.slq.qld.gov.au/api/{image_id}").json()
        preview_url = image_data['resources']['images'][0]['preview']
        id = [item for item in preview_url.split('/') if '.jpg' in item][0]
        fullsize_url = f"https://collections.slq.qld.gov.au/api/iiif/2/{id}/full/746,/0/default.jpg"
        response = requests.get(url=fullsize_url, stream=True)
        filename = filename or id
        with open(filename, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
            print(f"downloaded {filename}")
    except Exception as ex:
        print(f"Failed to load {filename}")

#https://onesearch.slq.qld.gov.au/discovery/search?query=any,contains,myer%20centre,NOT&query=any,contains,Frank%20and%20Eunice%20Corley%20House%20Photographs,AND&pfilter=rtype,exact,images,AND&tab=All&search_scope=slq_digital_collections&vid=61SLQ_INST:SLQ&facet=searchcreationdate,include,1902%7C,%7C2000&mode=advanced&offset=0

def search(query):
    params = {
        'limit':100,
        'sort':'rank',
        'q':f'any,contains,{query},NOT;any,contains,Frank and Eunice Corley House Photographs,AND;rtype,exact,images,AND',
        'blendFacetsSeparately':False,
        'disableCache':False,
        'getMore':0,
        'inst':'61SLQ_INST',
        'lang':'en',
        'newspapersActive':True,
        'newspapersSearch':False,
        'offset':0,
        'pcAvailability':False,
        'qExclude':'',
        'qInclude':'',
        'rapido':False,
        'refEntryActive':False,
        'rtaLinks':True,
        'scope':'slq_digital_collections',
        'searchInFulltextUserSelection':True,
        'skipDelivery':'Y',
        'tab':'All',
        'vid':'61SLQ_INST:SLQ'
    }
    response = requests.get(url=f"https://onesearch.slq.qld.gov.au/primaws/rest/pub/pnxs",params=params)
    results = response.json().get("docs",[])
    images = [(item.get("pnx",{}).get("addata",{}))for item in results]

    image_ids = [({'title':item.get("btitle")[0], 'image_id':item.get('oclcid')})for item in images]

    for item in image_ids:
        try:
            oclcid = [(id) for id in item.get('image_id') if 'ie' in id]
            item['image_id'] = f"ie{oclcid[0].split('ie')[1]}"
        except Exception as ex:
            pass

    return image_ids


def main():
    queryname = 'flood'
    data = search(queryname)
    if len(data) == 0:
        print("No results")
        return
    if not os.path.exists(queryname):
        os.makedirs(queryname)
    i = 0
    args_list = []
    for item in data:
        title = item['title'].replace('/','-')
        args_list.append((item['image_id'], F"{queryname}/{title}.jpg"))

    with Pool(4) as pool:
        pool.starmap(fetch_image, args_list)

    print(f"Files loaded")

if __name__ == '__main__':
    main()