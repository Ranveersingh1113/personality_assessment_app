"""
Safe DataFrame Access Utility

Provides safe access functions for pandas DataFrames to prevent:
- Division by zero errors
- Null pointer exceptions
- Index out of bounds errors
- Missing column errors
"""

import pandas as pd
import numpy as np
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


def safe_get_dataframe_value(
    df: pd.DataFrame,
    column: str,
    index: int = 0,
    default: Any = None,
    log_errors: bool = True
) -> Any:
    """
    Safely retrieve a value from a DataFrame with comprehensive error handling.
    
    Args:
        df: The DataFrame to access
        column: Column name to retrieve
        index: Row index (default: 0)
        default: Default value to return on error (default: None)
        log_errors: Whether to log errors (default: True)
    
    Returns:
        The value at df[column].iloc[index], or default if any error occurs
    
    Example:
        >>> value = safe_get_dataframe_value(df, 'Name', 0, default='Unknown')
    """
    try:
        # Check if DataFrame is empty
        if df is None or df.empty:
            if log_errors:
                logger.warning(f"DataFrame is empty when accessing column '{column}'")
            return default
        
        # Check if column exists
        if column not in df.columns:
            if log_errors:
                logger.warning(f"Column '{column}' not found in DataFrame. Available columns: {list(df.columns)}")
            return default
        
        # Check if index is valid
        if index < 0 or index >= len(df):
            if log_errors:
                logger.warning(f"Index {index} out of bounds for DataFrame with {len(df)} rows")
            return default
        
        # Get the value
        value = df[column].iloc[index]
        
        # Handle None/NaN values
        if pd.isna(value):
            if log_errors:
                logger.debug(f"Value at df['{column}'].iloc[{index}] is NaN/None, returning default")
            return default
        
        return value
        
    except Exception as e:
        if log_errors:
            logger.error(f"Error accessing df['{column}'].iloc[{index}]: {e}")
        return default


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely perform division with zero-check.
    
    Args:
        numerator: The numerator
        denominator: The denominator
        default: Value to return if denominator is zero (default: 0.0)
    
    Returns:
        numerator / denominator, or default if denominator is zero or invalid
    
    Example:
        >>> result = safe_divide(10, 2)  # Returns 5.0
        >>> result = safe_divide(10, 0)  # Returns 0.0
    """
    try:
        # Check for zero or invalid denominator
        if denominator == 0 or pd.isna(denominator) or np.isnan(denominator):
            logger.warning(f"Division by zero or invalid denominator: {denominator}, returning default: {default}")
            return default
        
        # Check for invalid numerator
        if pd.isna(numerator) or np.isnan(numerator):
            logger.warning(f"Invalid numerator: {numerator}, returning default: {default}")
            return default
        
        result = numerator / denominator
        
        # Check if result is valid
        if pd.isna(result) or np.isnan(result) or np.isinf(result):
            logger.warning(f"Division resulted in invalid value: {result}, returning default: {default}")
            return default
        
        return result
        
    except Exception as e:
        logger.error(f"Error in division {numerator}/{denominator}: {e}")
        return default


def safe_normalize_weights(weights: list, fallback_equal: bool = True) -> list:
    """
    Safely normalize a list of weights to sum to 1.0.
    
    Args:
        weights: List of weight values
        fallback_equal: If True, return equal weights on error (default: True)
    
    Returns:
        Normalized weights that sum to 1.0, or equal weights if normalization fails
    
    Example:
        >>> weights = safe_normalize_weights([1, 2, 3])  # Returns [0.167, 0.333, 0.5]
        >>> weights = safe_normalize_weights([0, 0, 0])  # Returns [0.333, 0.333, 0.333]
    """
    try:
        if not weights:
            return []
        
        # Calculate total weight
        total_weight = sum(weights)
        
        # Check for zero or invalid total
        if total_weight <= 0 or pd.isna(total_weight) or np.isnan(total_weight):
            logger.warning(f"Total weight is zero or invalid: {total_weight}, using fallback")
            if fallback_equal:
                # Return equal weights
                equal_weight = 1.0 / len(weights)
                return [equal_weight] * len(weights)
            else:
                return weights
        
        # Normalize weights
        normalized = [w / total_weight for w in weights]
        
        # Verify normalization
        normalized_sum = sum(normalized)
        if abs(normalized_sum - 1.0) > 0.01:  # Allow small floating point error
            logger.warning(f"Normalized weights sum to {normalized_sum}, not 1.0")
        
        return normalized
        
    except Exception as e:
        logger.error(f"Error normalizing weights: {e}")
        if fallback_equal and weights:
            equal_weight = 1.0 / len(weights)
            return [equal_weight] * len(weights)
        return weights


def safe_get_column_values(
    df: pd.DataFrame,
    column: str,
    default: Any = None,
    skip_na: bool = True
) -> list:
    """
    Safely retrieve all values from a DataFrame column.
    
    Args:
        df: The DataFrame to access
        column: Column name to retrieve
        default: Default value for missing/NaN entries
        skip_na: If True, skip NaN values (default: True)
    
    Returns:
        List of values from the column, with NaN handling
    
    Example:
        >>> values = safe_get_column_values(df, 'Name', default='Unknown')
    """
    try:
        # Check if DataFrame is empty
        if df is None or df.empty:
            logger.warning(f"DataFrame is empty when accessing column '{column}'")
            return []
        
        # Check if column exists
        if column not in df.columns:
            logger.warning(f"Column '{column}' not found in DataFrame")
            return []
        
        # Get column values
        values = df[column].tolist()
        
        # Handle NaN values
        if skip_na:
            values = [v for v in values if pd.notna(v)]
        else:
            values = [v if pd.notna(v) else default for v in values]
        
        return values
        
    except Exception as e:
        logger.error(f"Error accessing column '{column}': {e}")
        return []


def safe_check_value(value: Any, allow_none: bool = False, allow_nan: bool = False) -> bool:
    """
    Check if a value is valid (not None, not NaN, not empty string).
    
    Args:
        value: The value to check
        allow_none: If True, None is considered valid
        allow_nan: If True, NaN is considered valid
    
    Returns:
        True if value is valid, False otherwise
    
    Example:
        >>> safe_check_value("test")  # Returns True
        >>> safe_check_value(None)    # Returns False
        >>> safe_check_value(np.nan)  # Returns False
    """
    # Check for None
    if value is None:
        return allow_none
    
    # Check for NaN (works for numpy and pandas)
    try:
        if pd.isna(value):
            return allow_nan
    except:
        pass
    
    # Check for empty string
    if isinstance(value, str) and not value.strip():
        return False
    
    return True


def safe_get_first_valid_value(df: pd.DataFrame, column: str, default: Any = None) -> Any:
    """
    Get the first valid (non-NaN, non-None) value from a DataFrame column.
    
    Args:
        df: The DataFrame to access
        column: Column name to retrieve
        default: Default value if no valid value found
    
    Returns:
        First valid value, or default if none found
    
    Example:
        >>> value = safe_get_first_valid_value(df, 'Name', default='Unknown')
    """
    try:
        if df is None or df.empty or column not in df.columns:
            return default
        
        # Get all values
        values = df[column].tolist()
        
        # Find first valid value
        for value in values:
            if safe_check_value(value):
                return value
        
        return default
        
    except Exception as e:
        logger.error(f"Error getting first valid value from column '{column}': {e}")
        return default
