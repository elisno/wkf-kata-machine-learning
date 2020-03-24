import pandas as pd
import requests
from bs4 import BeautifulSoup


def category_data(category_url):

    """Collect basic information on draws for a category/round in a WKF event

    Args:
    category_url (str): url of the draws for the given gategory

    Yields:
    (tuple): tuple containing:

        tables (bs4.element.ResultSet): HTML tables for each pool in the category
        tournament (str): The WKF event in the draws page header
        category (str): The category (round + group) in the draws page header

   """

    # make http request to the site
    page = requests.get(category_url)
    # parse the html content
    soup = BeautifulSoup(page.content, 'html.parser')

    # Determine the tournament and category (optionally with group and round)
    tournament, category = soup.find_all("div", {"class": "newsheader"})[0].text[:-2].rsplit(" - ",1)

    # The round is split into pools. Pools are organized in separate tables.
    tables = soup.find_all("table", {"class": "moduletable_draw"})
    return tables, tournament, category


def get_round_performances(url):

    """Get round data from tables and save them in a dictionary

    Args:
    url (str):  url of the draws for the given gategory
        (identical to the argument in category_data(category_url))

    Yields:
    data (list[dict]):  List of athlete performances in a given round,
        each entry stored as a dict. For example:

        {'Tournament': "<Name of Competition> - <Location> <Date>",
         'Category': 'Male/Female Kata RX-GY'               # Useful for later rounds
         'Pool': '<Pool Number> / <Number of Pools>',       # Useful for first round
         'Name': '<Name of Competitor>',
         'Nationality': '<Country in abbr. in Alpha-3>',    # E.g. "JPN" or "ESP"
         'Kata': '<Kata number> <Kata Name>',               # E.g. "002 Anan Dai"
         'TEC1': <Technical Score from Judge 1>,            # Should have 7 scores
         ...,
         'ATH1': <Athletic Score from Judge 1>,             # Should have 7 scores
         ...,
         'Score': <Weighted Score>                          # Used for athlete ranking withing pool/group
         }

    """

    tables, tournament, category = category_data(url)

    # Collect kata performance data for each competitor in the round
    data = []
    for table in tables:
        pool = table.find_all("tr")[0].text.split(":")[1]
        performances = table.find_all("tr", {"class": ["dctabrowwhite", "dctabrowgreen"]})

        for k in range(len(performances)):
            performance = performances[k]
            competitor = performance.find_all("b")[0].text
            competitor_name = competitor.rsplit(" (",1)[0]
            nationality = competitor.rsplit(",",1)[-1][:-1]

            kata = performance.find_all("td")[2].text
            #print(competitor_name)

            # Missing data where registered competitors don't compete / get grades
            # Usually, the kata is announced at the start of the round
            # which guarantees that the competitor get's a score
            if (len(kata) > 0) and (len(performance.find_all("tr")) > 0):
                TEC, ATH = (performance.find_all("tr")[i].find_all("td") for i in range(2))
                technical_grades, athletic_grades = [grade.text for grade in TEC[1:8]], [grade.text for grade in ATH[1:8]]
                technical_score, athletic_score = float(TEC[-1].text), float(ATH[-1].text)
                total_score = float(performance.find_all("td")[-1].text)
                #float(total_score)
                technical_grades = [float(i.replace(',', '.')) for i in technical_grades]
                athletic_grades = [float(i.replace(',', '.')) for i in athletic_grades]


                perf_data = {'Tournament':tournament,
                        'Category':category,
                        'Pool':pool,
                        'Name':competitor_name,
                        'Nationality':nationality,
                        "Kata":kata
                       }

                TEC_names = ["TEC" + str(i+1) for i in range(0, len(technical_grades))]
                ATH_names = ["ATH" + str(i+1) for i in range(0, len(athletic_grades))]
                perf_data.update(dict(zip(TEC_names,technical_grades)))
                perf_data.update(dict(zip(ATH_names,athletic_grades)))
                perf_data.update({"Score":total_score})

                #perf_df = pd.DataFrame(perf_data)
                data.append(perf_data)

    return data

def get_rounds_urls(draws_url):

    """Collects urls to be used by get_round_performances(url) for a given WKF event

    Args:
    draws_url (str): Page url that links to all categories (kata + kumite) for the WKF event

    Yields:
    urls (list[str]): A list of urls for draws in kata categories in a WKF event.

    """
    page = requests.get(draws_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    datalink2s = soup.find_all("a",{"class": "datalink2"})[:-3]
    urls = []
    for link in datalink2s:
        if ("Male Kata" in link['title']) or ("Female Kata" in link['title']):
            urls.append("https://www.sportdata.org/wkf/set-online/" + link['href'])
    return urls


def get_performances(draws_url):

    """Goes through all kata categories and concatenates all athlete performances in a Pandas DataFrame

    Args:
    draws_url (str): Page url that links to all categories (kata + kumite) for the WKF event

    Yields:
    (pandas.core.frame.DataFrame): A DataFrame of all athlete kata performances for the WKF event

    """

    urls = get_rounds_urls(draws_url)

    # Make DataFrame from each category / round
    data_rounds = [pd.DataFrame(get_round_performances(i)) for i in urls]

    # Concatenate categories / rounds
    return pd.concat(data_rounds)

def concat_tournaments(filename):
    """Collect kata performances list of draws urls for multiple WKF events

    Args:
    filename (str): Name of a file containing all urls for event draws

    Yields:
    df (pandas.core.frame.DataFrame): A DataFrame containing all
        kata performances from WKF events specified in `filename`

    Results from this method are typically stored in a file, e.g. `filename.csv`
    """

    f  = open(filename,"r")
    draws_urls = f.read().splitlines()
    f.close()
    df = pd.concat([get_performances(url) for url in draws_urls])
    return df


if __name__ == "__main__":

    from os.path import isfile

    premier_league_csv = "premier_league.csv"
    if isfile(premier_league_csv):
        print("File '%s' already exists" % premier_league_csv)
    else:
        premier_league_file = "premier-league.txt"
        premier_league_df = concat_tournaments(premier_league_file)
        premier_league_df.to_csv(premier_league_csv, index=False)

    series_A_csv = "series_A.csv"
    if isfile(series_A_csv):
        print("File '%s' already exists" % series_A_csv)
    else:
        series_A_file = "series-A.txt"
        series_A_df = concat_tournaments(series_A_file)
        series_A_df.to_csv(series_A_csv, index=False)
