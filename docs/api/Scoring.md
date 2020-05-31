
# rapidminer


## Scoring

Class that allows you to use the Real-Time Scoring agent directly on a dataset.



```python
Scoring(hostname, endpoint)
```

Arguments:
- `hostname`: Server url (together with the port)
- `endpoint`: scoring service endpoint to use


### predict
```python
Scoring.predict(dataframe)
```

Calls the Real-Time Scoring agent on the specified dataset and returns the result.

Arguments:
- `dataframe`: the pandas DataFrame.



Returns:


- the result as a pandas DataFrame.
