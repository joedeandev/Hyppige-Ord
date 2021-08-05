# De Hyppigste Ord i den Frie Encyklopædi

Danish word frequency list generated from [da.wikipedia.org](https://da.wikipedia.org/).

## Files

* [da-words.csv](./da-words.csv) lists 1,849,899 case-sensitive words, the number of times they appear in the data set, and their relative frequency.
* [da-words-nocase.csv](./da-words.csv) contains the same information, but case-insensitive.


The text has been filtered with a "quality over quantity approach", filtering out any text in a MediaWiki template or anything that looks like a URL. Only words consisting solely of the following characters are included: `abcdefghijklmnopqrstuvwxyzæøåABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅéÉ-` (accents and special characters included according to [Dansk Sprognævn](https://dsn.dk/ordboeger/retskrivningsordbogen/%C2%A7-1-6-bogstaver-og-tegn/%C2%A7-2-tegn/)).

## Usage

This can be run via the command line (use the `-h` flag for help). 

Data dumps from [da.wikipedia.org](https://da.wikipedia.org/) can be downloaded from [dumps.wikimedia.org](https://dumps.wikimedia.org/dawiki/). You'll likely want the first download on the list, "Articles, templates, media/file descriptions, and primary meta-pages" (something like `dawiki-20210720-pages-articles-multistream.xml.bz2`).

The collected word data is saved in a SQLite database (to make other data exploration significantly faster), and then exported to CSV files.

## Alternatives

* [De hyppigste ord i dansk](https://korpus.dsl.dk/resources/details/freq-lemmas.html) is a more academic resource, but lists only 10,000 words.

* [Wikitionary's Danish wordlist](https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Danish_wordlist) is based on subtitles, and may give a better representation of colloquial usage.
