import os

class PropertiesConfig:
    """
    Parses and exposes keys from the config.properties file.
    """
    def __init__(self, filename="config.properties"):
        self.properties = {}
        # Get path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(current_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('//') and '=' in line:
                        key, val = line.split('=', 1)
                        self.properties[key.strip()] = val.strip()

    def get(self, key, default=None):
        return self.properties.get(key, default)

# Global configuration instance
app_config = PropertiesConfig()
