"""
Rule-based alerting system for stock price monitoring.
Triggers alerts based on configurable thresholds and conditions.
"""
import os
from datetime import datetime
from logs.logger import setup_logger

logger = setup_logger(__name__, 'alerts.log')


class AlertRule:
    """Base class for alert rules"""
    
    def __init__(self, rule_name, enabled=True):
        self.rule_name = rule_name
        self.enabled = enabled
    
    def check(self, stock_data):
        """Override this method to implement rule logic"""
        raise NotImplementedError


class PriceDropAlert(AlertRule):
    """Alert when price drops below a threshold percentage"""
    
    def __init__(self, threshold_percent=5.0, enabled=True):
        super().__init__("PriceDropAlert", enabled)
        self.threshold_percent = threshold_percent
    
    def check(self, stock_data):
        """Check if price dropped significantly"""
        if not self.enabled or not stock_data:
            return None
        
        open_price = stock_data.get("open")
        close_price = stock_data.get("close")
        stock = stock_data.get("stock")
        
        if open_price and close_price and open_price > 0:
            drop_percent = ((open_price - close_price) / open_price) * 100
            if drop_percent >= self.threshold_percent:
                message = f"ALERT: {stock} dropped {drop_percent:.2f}% (Open: ${open_price:.2f}, Close: ${close_price:.2f})"
                logger.warning(message)
                return {
                    "rule": self.rule_name,
                    "stock": stock,
                    "severity": "HIGH",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
        return None


class PriceSpikeAlert(AlertRule):
    """Alert when price increases above a threshold percentage"""
    
    def __init__(self, threshold_percent=5.0, enabled=True):
        super().__init__("PriceSpikeAlert", enabled)
        self.threshold_percent = threshold_percent
    
    def check(self, stock_data):
        """Check if price spiked significantly"""
        if not self.enabled or not stock_data:
            return None
        
        open_price = stock_data.get("open")
        close_price = stock_data.get("close")
        stock = stock_data.get("stock")
        
        if open_price and close_price and open_price > 0:
            spike_percent = ((close_price - open_price) / open_price) * 100
            if spike_percent >= self.threshold_percent:
                message = f"ALERT: {stock} spiked {spike_percent:.2f}% (Open: ${open_price:.2f}, Close: ${close_price:.2f})"
                logger.warning(message)
                return {
                    "rule": self.rule_name,
                    "stock": stock,
                    "severity": "MEDIUM",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
        return None


class HighVolumeAlert(AlertRule):
    """Alert when trading volume exceeds threshold"""
    
    def __init__(self, threshold_volume=1000000, enabled=True):
        super().__init__("HighVolumeAlert", enabled)
        self.threshold_volume = threshold_volume
    
    def check(self, stock_data):
        """Check if volume exceeds threshold"""
        if not self.enabled or not stock_data:
            return None
        
        volume = stock_data.get("volume")
        stock = stock_data.get("stock")
        
        if volume and volume >= self.threshold_volume:
            message = f"ALERT: {stock} high volume detected: {volume:,.0f} shares"
            logger.info(message)
            return {
                "rule": self.rule_name,
                "stock": stock,
                "severity": "INFO",
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        return None


class VolatilityAlert(AlertRule):
    """Alert when price volatility (high-low spread) exceeds threshold"""
    
    def __init__(self, threshold_percent=3.0, enabled=True):
        super().__init__("VolatilityAlert", enabled)
        self.threshold_percent = threshold_percent
    
    def check(self, stock_data):
        """Check if volatility exceeds threshold"""
        if not self.enabled or not stock_data:
            return None
        
        high = stock_data.get("high")
        low = stock_data.get("low")
        stock = stock_data.get("stock")
        
        if high and low and low > 0:
            volatility_percent = ((high - low) / low) * 100
            if volatility_percent >= self.threshold_percent:
                message = f"ALERT: {stock} high volatility detected: {volatility_percent:.2f}% (High: ${high:.2f}, Low: ${low:.2f})"
                logger.warning(message)
                return {
                    "rule": self.rule_name,
                    "stock": stock,
                    "severity": "MEDIUM",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
        return None


class AlertEngine:
    """Main alert engine that manages and executes alert rules"""
    
    def __init__(self):
        self.rules = []
        self.alert_history = []
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        self.rules = [
            PriceDropAlert(threshold_percent=5.0, enabled=True),
            PriceSpikeAlert(threshold_percent=5.0, enabled=True),
            HighVolumeAlert(threshold_volume=1000000, enabled=True),
            VolatilityAlert(threshold_percent=3.0, enabled=True)
        ]
        logger.info(f"Initialized {len(self.rules)} alert rules")
    
    def add_rule(self, rule):
        """Add a custom alert rule"""
        self.rules.append(rule)
        logger.info(f"Added custom rule: {rule.rule_name}")
    
    def process_stock_data(self, stock_data):
        """Process stock data through all enabled alert rules"""
        alerts_triggered = []
        
        for rule in self.rules:
            try:
                alert = rule.check(stock_data)
                if alert:
                    alerts_triggered.append(alert)
                    self.alert_history.append(alert)
            except Exception as e:
                logger.error(f"Error executing rule {rule.rule_name}: {str(e)}")
        
        return alerts_triggered
    
    def get_alert_count(self):
        """Get total number of alerts triggered"""
        return len(self.alert_history)
    
    def get_recent_alerts(self, count=10):
        """Get most recent alerts"""
        return self.alert_history[-count:]
