from wkf_kata_machine_learning.data_utils import category_data, get_rounds_urls


def test_category_data():
    url = "https://www.sportdata.org/wkf/set-online/popup_mitschrift_main.php?popup_action=auslosungcatpunktexml&catid=36&verid=381"
    tables, tournament, category = category_data(url)
    assert len(tables) == 4
    assert tournament == "Karate1 Premier League - Salzburg 2020"
    assert category == "Female Kata"

def test_get_rounds_urls():
    draws_url = "https://www.sportdata.org/wkf/set-online/veranstaltung_info_main.php?active_menu=calendar&vernr=381&ver_info_action=catauslist#a_eventheadend"
    # There should be 16 distinct rounds in individual kata on the given tournament
    assert len(get_rounds_urls(draws_url)) == 16
