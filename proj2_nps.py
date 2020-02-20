import requests
import json
from bs4 import BeautifulSoup
import secrets
import plotly.plotly as py
import plotly.graph_objs as go



## proj_nps.py
## Skeleton for Project 2, Winter 2018
## ~~~ modify this file, but don't rename it ~~~

key = secrets.google_places_key

CACHE_FNAME = 'cachefile.json'
try:
    with open(CACHE_FNAME, 'r') as f:
        cache = f.read()
        CACHE_DICTION = json.loads(cache)
        f.close()
except:
    CACHE_DICTION = {}

def unique_key(url):
    return url

def make_request_using_cache(url):
    unique_ident = unique_key(url)
    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]
    else:
        resp = requests.get(url)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        with open(CACHE_FNAME, 'w') as fw:
            fw.write(dumped_json_cache)
            fw.close()
        return CACHE_DICTION[unique_ident]

def params_unique_combination(baseurl,parameters):
    alphabetized_keys = sorted(parameters.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, parameters[k]))
    return baseurl + "_".join(res)

class NationalSite():
    def __init__(self, type, name, desc, burl=None):
        self.type = type
        self.name = name
        self.desc = desc
        self.burl = burl

        try:
            site_req = make_request_using_cache(self.burl)
            site_soup = BeautifulSoup(site_req, 'html.parser')
            site_soup2 = site_soup.find(class_='mailing-address')
            self.address_street = site_soup2.find('span', itemprop='streetAddress').text.strip()
            self.address_city = site_soup2.find('span', itemprop='addressLocality').text.strip()
            self.address_state = site_soup2.find('span', itemprop='addressRegion').text.strip()
            self.address_zip = site_soup2.find('span', itemprop='postalCode').text.strip()
        except:
            pass

    def __str__(self):
        try:
            return "{} ({}): {}, {}, {} {}".format(self.name, self.type, self.address_street, self.address_city, self.address_state, self.address_zip)
        except:
            return "No address"

## you can, and should add to and modify this class any way you see fit
## you can add attributes and modify the __init__ parameters,
##   as long as tests still pass
##
## the starter code is here just to make the tests run (and fail)
class NearbyPlace():
    def __init__(self, name, lat, lon):
        self.name = name
        self.lat = lat
        self.lon = lon

    def get_loc(self):
        return [self.lat, self.lon]

    def __str__(self):
        return self.name

## Must return the list of NationalSites for the specified state
## param: the 2-letter state abbreviation, lowercase
##        (OK to make it work for uppercase too)
## returns: all of the NationalSites
##        (e.g., National Parks, National Heritage Sites, etc.) that are listed
##        for the state at nps.gov


def get_sites_for_state(state_abbr):
    baseurl = 'https://www.nps.gov/index.htm'
    info = make_request_using_cache(baseurl)
    soup = BeautifulSoup(info, 'html.parser')
    soup_dropdown = soup.find(class_='dropdown-menu SearchBar-keywordSearch')
    state_lst = soup_dropdown.find_all('li')
    for state in state_lst:
        adl_url = state.find('a')['href']
        new_url = "https://www.nps.gov"
        req_url = new_url+adl_url
        if req_url[26:28] == state_abbr.lower():
            state_info = make_request_using_cache(req_url)
            state_info_soup = BeautifulSoup(state_info, 'html.parser')
            crawl_site = state_info_soup.find(class_='col-md-9 col-sm-12 col-xs-12 stateCol')
            crawl_site2 = crawl_site.find_all('li')
            list_of_st_sites = []
            for site in crawl_site2:
                try:
                    site_url = site.find('h3')
                    if site_url != None:
                        site_url2 = site_url.find('a')['href']
                        site_specific_url = site_url2
                        burl = 'https://www.nps.gov{}index.htm'.format(site_specific_url)
                        site_req = make_request_using_cache(burl)
                        site_soup = BeautifulSoup(site_req, 'html.parser')
                        site_name = site_soup.find(class_='Hero-title').text.strip()
                        site_type = site_soup.find(class_='Hero-designation').text.strip()
                        site_desc = site_soup.find(class_='Component text-content-size text-content-style').text.strip()
                        x = NationalSite(site_type, site_name, site_desc, burl)
                        list_of_st_sites.append(x)
                except:
                    pass
    return list_of_st_sites

## Must return the list of NearbyPlaces for the specifite NationalSite
## param: a NationalSite object
## returns: a list of NearbyPlaces within 10km of the given site
##          if the site is not found by a Google Places search, this should
##          return an empty list

def get_nearby_places_for_site(national_site):
    list_of_nearby_sites = []
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params_dict = {}
    params_dict['query'] = national_site.name
    params_dict['key'] = key
    u = params_unique_combination(base_url, params_dict)
    if u in CACHE_DICTION:
        print('getting cache')
    else:
        #print('writing cache')
        response = requests.get(base_url, params=params_dict)
        content = response.text
        pyt_obj = json.loads(content)
        CACHE_DICTION[u] = pyt_obj
        dumped_json_cache = json.dumps(CACHE_DICTION)
        with open(CACHE_FNAME, 'w') as f:
            f.write(dumped_json_cache)
            f.close()
    list_from_req = CACHE_DICTION[u]['results']
    latitude = list_from_req[0]['geometry']['location']['lat']
    longitude = list_from_req[0]['geometry']['location']['lng']
    loc = str(latitude) + ',' + str(longitude)
    params = {}
    params['key'] = key
    params['location'] = loc
    params['radius'] = 10000
    base_url2 = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    unique = params_unique_combination(base_url2,params)
    if unique in CACHE_DICTION:
        print('getting cache')
    else:
        #print('writing cache')
        response2 = requests.get(base_url2, params=params)
        content2 = response2.text
        pyt_obj2 = json.loads(content2)
        CACHE_DICTION[unique] = pyt_obj2
        dumped_json_cache2 = json.dumps(CACHE_DICTION)
        with open(CACHE_FNAME, 'w') as f:
            f.write(dumped_json_cache2)
            f.close()
    list_from_req2 = CACHE_DICTION[unique]['results']
    counter = 0
    while counter < len(list_from_req2):
        for d in list_from_req2:
            name = list_from_req2[counter]['name']
            lat_ = list_from_req2[counter]['geometry']['location']['lat']
            lon_ = list_from_req2[counter]['geometry']['location']['lng']
            name_loc = NearbyPlace(name, lat_, lon_)
            list_of_nearby_sites.append(name_loc)
            counter += 1

    return list_of_nearby_sites

## Must plot all of the NationalSites listed for the state on nps.gov
## Note that some NationalSites might actually be located outside the state.
## If any NationalSites are not found by the Google Places API they should
##  be ignored.
## param: the 2-letter state abbreviation
## returns: nothing
## side effects: launches a plotly page in the web browser

def get_site_lat_lon(national_site_obj):
    list_of_sites = []
    CACHE_FNAME2 = 'cachefile2.json'
    try:
        with open(CACHE_FNAME2, 'r') as r:
            contents = r.read()
            CACHE_DICTION = json.loads(contents)
            r.close()
    except:
        CACHE_DICTION = {}

    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params_dict = {}
    params_dict['query'] = national_site_obj.name
    params_dict['key'] = key
    u = params_unique_combination(base_url,params_dict)
    if u in CACHE_DICTION:
        print("getting cache")
    else:
        #print('writing cache')
        response = requests.get(base_url, params=params_dict)
        content = response.text
        pyt_obj = json.loads(content)
        CACHE_DICTION[u] = pyt_obj
        dumped_json_cache = json.dumps(CACHE_DICTION)
        with open(CACHE_FNAME2, 'w') as fw:
            fw.write(dumped_json_cache)
            fw.close()
    list_from_req = CACHE_DICTION[u]['results']
    loc_lst = []
    for x in list_from_req:
        latitude = list_from_req[0]['geometry']['location']['lat']
        longitude = list_from_req[0]['geometry']['location']['lng']
        loc_lst.append(latitude)
        loc_lst.append(longitude)
    list_of_sites.append(loc_lst)
    return list_of_sites

def plot_sites_for_state(state_abbr):
    lst = []
    lat_lst = []
    lon_lst = []
    text_list = []
    text_list2 = []
    info = get_sites_for_state(state_abbr)
    for x in info:
        info_location = get_site_lat_lon(x)
        lst.append(info_location)
        text_list.append(str((x.name)))
    new_lst = zip(lst, text_list)
    for place in list(new_lst):
        if place[0][0]:
            lat_lst.append(place[0][0][0])
            lon_lst.append(place[0][0][1])
            text_list2.append(place[1])

    data = [dict(
            type = 'scattergeo',
            locationmode = 'USA-states',
            lon = lon_lst,
            lat = lat_lst,
            text = text_list2,
            mode = 'markers',
            marker = dict(
                size = 10,
                symbol = 'circle',
                color = 'blue'
            ))]

    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    for str_v in lat_lst:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in lon_lst:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
    padding = max_range * .10
    lat_axis = [min_lat - padding, max_lat + padding]
    lon_axis = [min_lon - padding, max_lon + padding]

    layout = dict(
            title = 'National Sites<br>(Hover for names)',
            geo = dict(
                scope='usa',
                projection=dict( type='albers usa' ),
                showland = True,
                landcolor = "rgb(250, 250, 250)",
                subunitcolor = "rgb(100, 217, 217)",
                countrycolor = "rgb(217, 100, 217)",
                lataxis = {'range': lat_axis},
                lonaxis = {'range': lon_axis},
                center = {'lat': center_lat, 'lon': center_lon },
                countrywidth = 3,
                subunitwidth = 3
            ),
        )

    figure = dict(data=data, layout=layout)
    py.plot(figure, validate=False, filename='national sites ' + state_abbr)

    return None


## Must plot up to 20 of the NearbyPlaces found using the Google Places API
## param: the NationalSite around which to search
## returns: nothing
## side effects: launches a plotly page in the web browser

def plot_nearby_for_site(site_object):
    site_loc = get_site_lat_lon(site_object)
    site_lat = []
    site_lat.append(site_loc[0][0])
    site_lon = []
    site_lon.append(site_loc[0][1])
    site_name = []
    site_name.append(site_object.name)
    lst = []
    lat_lst = []
    lon_lst = []
    text_list = []
    text_list2 = []
    nearby_sites = get_nearby_places_for_site(site_object)
    for x in nearby_sites:
        info_location = x.get_loc()
        lst.append(info_location)
        text_list.append(str(x.name))
    new_lst = zip(lst, text_list)
    for place in list(new_lst):
        if place[0]:
            if place[0][0] != site_loc[0][0]:
                if place[0][1] != site_loc[0][1]:
                    lat_lst.append(place[0][0])
                    lon_lst.append(place[0][1])
                    text_list2.append(place[1])

    trace1 = dict(
            type = 'scattergeo',
            locationmode = 'USA-states',
            lon = lon_lst,
            lat = lat_lst,
            text = text_list2,
            mode = 'markers',
            marker = dict(
                size = 7,
                symbol = 'circle',
                color = 'blue'
            ))

    trace2 = dict(
            type = 'scattergeo',
            locationmode = 'USA-states',
            lon = site_lon,
            lat = site_lat,
            text = site_name,
            mode = 'markers',
            marker = dict(
                size = 10,
                symbol = 'star',
                color = 'red'
            ))

    data = [trace2, trace1]

    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    for str_v in lat_lst:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in lon_lst:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
    padding = max_range * .80
    lat_axis = [min_lat - padding, max_lat + padding]
    lon_axis = [min_lon - padding, max_lon + padding]

    layout = dict(
            title = 'Nearby Sites<br>(Hover for names)',
            geo = dict(
                scope='usa',
                projection=dict( type='albers usa' ),
                showland = True,
                landcolor = "rgb(250, 250, 250)",
                subunitcolor = "rgb(100, 217, 217)",
                countrycolor = "rgb(217, 100, 217)",
                lataxis = {'range': lat_axis},
                lonaxis = {'range': lon_axis},
                center = {'lat': center_lat, 'lon': center_lon },
                countrywidth = 3,
                subunitwidth = 3
            ),
        )

    fig = dict(data=data, layout=layout)
    py.plot(fig, validate=False, filename='nearby sites for' + site_object.name)

    return None

if __name__ == "__main__":
    current_bool = True
    available_commands = "1. list <state abbreviation> : available at anytime to list all National sites in a state\n Valid input is two letter state abbreviation\n 2. nearby <result_number> : available only with an active result set\n Lists all places near a national site\n Valid input is a number in the list from the results above\n 3. map : available only if there is an active result set\n Displays current results on a map\n 4. exit : exits the program\n 5. help: lists available commands"

    lst_of_val_st = ['list al', 'list az', 'list ak', 'list ar', 'list ca', 'list co', 'list ct', 'list de', 'list fl', 'list ga', 'list hi', 'list id', 'list il', 'list in', 'list ia', 'list ks', 'list ky', 'list la', 'list me', 'list md', 'list ma', 'list mi', 'list mn', 'list ms', 'list mo', 'list mt', 'list ne', 'list nv', 'list nh', 'list nj', 'list nm', 'list ny', 'list nc', 'list nd', 'list oh', 'list ok', 'list or', 'list pa', 'list ri', 'list sc', 'list sd', 'list tn', 'list tx', 'list ut', 'list vt', 'list va', 'list wa', 'list wv', 'list wi', 'list wy']

    def user_input():
        user_input = input("Enter a command, 'help' for available commands, or 'exit' to quit: ")
        lower = user_input.lower()
        split = lower.split()
        return split

    inp = user_input()

    site_st_list = []
    nearby_site_list = []

    while inp[0] != 'exit':
        if inp[0] == 'help':
            print(available_commands)
            inp = user_input()
            continue
        elif inp[0] == 'list':
            state = str(inp[0] + ' ' + inp[1])
            if state in lst_of_val_st:
                site_st_list = get_sites_for_state(state[5:])
                counter = 1
                for site in range(len(site_st_list)):
                    print(counter, site_st_list[site])
                    counter += 1
                inp = user_input()
                if inp[0] == 'map':
                    plot_sites_for_state(state[5:])
                    inp = user_input()
            else:
                print("That input was incorrect, please enter a valid input")
                inp = user_input()
        elif inp[0] == 'nearby':
            if len(site_st_list) == 0:
                print("No active result set. Please start a new search.")
                inp = user_input()
            else:
                nearby_number = int(inp[1]) - 1
                nearby_list = get_nearby_places_for_site(site_st_list[nearby_number])
                print("Places near " + str(site_st_list[nearby_number].name) + "...")
                counter = 1
                for x in range(len(nearby_list)):
                    print(counter, nearby_list[x])
                    counter += 1
                inp = user_input()
                if inp[0] == 'map':
                    plot_nearby_for_site(site_st_list[nearby_number])
                    inp = user_input()
        elif inp[0] == 'map':
            if len(site_st_list) == 0:
                print("No active result set. Please start a new search.")
                inp = user_input()
            elif len(site_st_list) > 0:
                plot_sites_for_state(state[5:])
                inp = user_input()
        elif inp[0] == 'exit':
            print('Bye')
            break
        else:
            print("That input was incorrect, please enter a valid input")
            inp = user_input()
