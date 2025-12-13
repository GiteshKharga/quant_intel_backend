
import numpy as np
import pandas as pd
from flask.json.provider import DefaultJSONProvider

class NumpyJSONProvider(DefaultJSONProvider):
    """
    Custom JSON provider to handle Numpy and Pandas types.
    """
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, pd.Series):
            return obj.to_list()
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
        return super().default(obj)
