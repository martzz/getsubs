# getsubs

A helper script (python 2.7) to find and download movie subtitles.

## Subtitle lookup

This app uses opensubtitles.org to search for the requested subltitles. There are 2 possible ways how to do that:

- Hash code lookup (-p) - A hash code is calculated out of the movie file and used in the subtitle search. This method
  is preferred since the lookup results almost always match the right movie version (fps, codecs, etc.) and the subtitle
  timing is correct.
- IMDB ID lookup (-i) - A lookup based on IMDB ID, which can be obtained from the imdb.com URL. First, find the movie on
  imdb.com and then copy the ID (for instance: https://www.imdb.com/title/tt6644200/, where the tt6644200 is what we
  need). Please note this search method is not that accurate as the hash code lookup, thus there can be many results
  that don't match with your move version and where the timing is not good.

### API

http://api.opensubtitles.org/xml-rpc

## Other options

You can specify the subtitle language as well as the output encoding. See the usage help:

```
$ python getsubs2.py -h
usage: getsubs2.py [-h] [-l LANGUAGE] [-e ENCODING] [-p PATH] [-i IMDB_ID]
                   output_dir

positional arguments:
  output_dir            Path of the output directory.

optional arguments:
  -h, --help            show this help message and exit
  -l LANGUAGE, --language LANGUAGE
                        Subtitles language (e.g. eng, cze) - default english.
  -e ENCODING, --encoding ENCODING
                        Convert to a specific character encoding (e.g. utf-8,
                        latin-1).
  -p PATH, --path PATH  Directory containing the movie (subtitle search using
                        hash of the movie). Use this option to get correctly
                        timed subtitles.
  -i IMDB_ID, --imdb_id IMDB_ID
                        Imdb id of the movie (subtitle search using imdb id).
                        Imdb id could be obtained from the imdb.com url:
                        https://www.imdb.com/title/tt2210497/ where 2210497 is
                        the id.
```


