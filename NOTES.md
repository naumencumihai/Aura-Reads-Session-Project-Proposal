## Notes on this repo

I started by wanting to just create the project memo, but then I also started thinkering/working on some initial test cases.
Gemini API free-tier seems to consistently fail when trying to analyze a full book (The Divine Comedy used as an example) instead i ran the analysis on the 0.json chunked_result where i left only 10 chunks and it seems to work just fine 👍.

This is showcasing the need for further chunking of the paragraphs to fit the models context and for a localy run LLModel. This approach will also allow for further training, better evaluation and observability

It's a start for what, I hope, will become a working and, possibly, marketable application. 😊
