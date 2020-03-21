datafiles=premier_league.csv series_A.csv


all: premier_league.csv series_A.csv


premier_league.csv: premier-league.txt
	python data_utils.py

series_A.csv: series-A.txt
	python data_utils.py

clean:
	rm $(datafiles)
