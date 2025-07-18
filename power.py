def power(a, b):
    """
    Calculate a raised to the power of b.
    
    Args:
        a: The base number
        b: The exponent
        
    Returns:
        a to the power of b
    """
    return a ** b

# Example usage
if __name__ == "__main__":
    # Example values
    a = 2
    b = 3
    result = power(a, b)
    print(f"{a} raised to the power of {b} equals {result}")