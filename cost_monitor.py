"""
Real-Time Cost Monitoring & Protection System
Tracks API costs vs revenue and protects against runaway expenses
"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import time

class CostMonitor:
    def __init__(self, db_path='cost_monitor.db'):
        self.db_path = db_path
        self.init_database()
        
        # Alert thresholds
        self.HOURLY_COST_LIMIT = 50.00
        self.DAILY_COST_LIMIT = 500.00
        self.PROFIT_MARGIN_MIN = 0.20  # 20% minimum
        
        # Emergency shutdown
        self.emergency_mode = False
    
    def init_database(self):
        """Create monitoring tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API cost tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                api_service TEXT,
                operation TEXT,
                cost REAL,
                success BOOLEAN,
                request_id TEXT
            )
        ''')
        
        # Revenue tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                amount REAL,
                type TEXT,
                description TEXT
            )
        ''')
        
        # Hourly summaries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hourly_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hour_start TIMESTAMP,
                total_cost REAL,
                total_revenue REAL,
                profit REAL,
                margin REAL,
                requests_count INTEGER,
                unique_users INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_api_cost(self, user_id, api_service, operation, cost, success=True, request_id=None):
        """Log every API call cost"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_costs (user_id, api_service, operation, cost, success, request_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, api_service, operation, cost, success, request_id))
        
        conn.commit()
        conn.close()
        
        # Check if costs are too high
        self.check_cost_alerts()
    
    def log_revenue(self, user_id, amount, revenue_type, description):
        """Log revenue (subscription, credit purchase, etc.)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO revenue (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, revenue_type, description))
        
        conn.commit()
        conn.close()
    
    def get_hourly_stats(self):
        """Get current hour statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        hour_ago = datetime.now() - timedelta(hours=1)
        
        # Total costs this hour
        cursor.execute('''
            SELECT SUM(cost), COUNT(*), COUNT(DISTINCT user_id)
            FROM api_costs
            WHERE timestamp > ?
        ''', (hour_ago,))
        
        cost_data = cursor.fetchone()
        total_cost = cost_data[0] or 0
        request_count = cost_data[1] or 0
        unique_users = cost_data[2] or 0
        
        # Total revenue this hour
        cursor.execute('''
            SELECT SUM(amount)
            FROM revenue
            WHERE timestamp > ?
        ''', (hour_ago,))
        
        total_revenue = cursor.fetchone()[0] or 0
        
        conn.close()
        
        profit = total_revenue - total_cost
        margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'hour_start': hour_ago.strftime('%Y-%m-%d %H:00:00'),
            'total_cost': round(total_cost, 2),
            'total_revenue': round(total_revenue, 2),
            'profit': round(profit, 2),
            'margin': round(margin, 1),
            'requests': request_count,
            'users': unique_users,
            'cost_per_request': round(total_cost / request_count, 4) if request_count > 0 else 0
        }
    
    def get_daily_stats(self):
        """Get today's statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Costs today
        cursor.execute('''
            SELECT SUM(cost), COUNT(*), COUNT(DISTINCT user_id)
            FROM api_costs
            WHERE timestamp > ?
        ''', (today,))
        
        cost_data = cursor.fetchone()
        total_cost = cost_data[0] or 0
        request_count = cost_data[1] or 0
        unique_users = cost_data[2] or 0
        
        # Revenue today
        cursor.execute('''
            SELECT SUM(amount)
            FROM revenue
            WHERE timestamp > ?
        ''', (today,))
        
        total_revenue = cursor.fetchone()[0] or 0
        
        conn.close()
        
        profit = total_revenue - total_cost
        margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'date': today.strftime('%Y-%m-%d'),
            'total_cost': round(total_cost, 2),
            'total_revenue': round(total_revenue, 2),
            'profit': round(profit, 2),
            'margin': round(margin, 1),
            'requests': request_count,
            'users': unique_users,
            'profitable': profit > 0
        }
    
    def check_cost_alerts(self):
        """Check if costs exceed safe thresholds"""
        hourly = self.get_hourly_stats()
        daily = self.get_daily_stats()
        
        alerts = []
        
        # Hourly cost alert
        if hourly['total_cost'] > self.HOURLY_COST_LIMIT:
            alerts.append({
                'level': 'WARNING',
                'message': f"Hourly costs: ${hourly['total_cost']} (limit: ${self.HOURLY_COST_LIMIT})"
            })
        
        # Daily cost circuit breaker
        if daily['total_cost'] > self.DAILY_COST_LIMIT:
            alerts.append({
                'level': 'CRITICAL',
                'message': f"Daily costs: ${daily['total_cost']} exceeded ${self.DAILY_COST_LIMIT} - EMERGENCY MODE ACTIVATED"
            })
            self.activate_emergency_mode()
        
        # Negative profit alert
        if hourly['profit'] < 0 and hourly['requests'] > 10:
            alerts.append({
                'level': 'WARNING',
                'message': f"Losing money! Hourly profit: ${hourly['profit']} ({hourly['margin']}% margin)"
            })
        
        # Low margin alert
        if hourly['margin'] > 0 and hourly['margin'] < self.PROFIT_MARGIN_MIN * 100:
            alerts.append({
                'level': 'INFO',
                'message': f"Low margin: {hourly['margin']}% (target: {self.PROFIT_MARGIN_MIN * 100}%)"
            })
        
        # Log alerts
        if alerts:
            self.send_alerts(alerts)
        
        return alerts
    
    def activate_emergency_mode(self):
        """Emergency shutdown to prevent runaway costs"""
        if self.emergency_mode:
            return  # Already in emergency mode
        
        self.emergency_mode = True
        
        # Log emergency activation
        print("🚨 EMERGENCY MODE ACTIVATED - Daily cost limit exceeded!")
        print("Actions taken:")
        print("- Disabled DALL-E 3 (using free Flux/SD only)")
        print("- Disabled premium video generation")
        print("- Reduced free tier from 10 to 5 images/day")
        print("- Enabled request queueing")
        
        # This will be imported and checked in rootAI.py
        with open('emergency_mode.flag', 'w') as f:
            f.write(str(datetime.now()))
    
    def deactivate_emergency_mode(self):
        """Restore normal operation"""
        import os
        
        self.emergency_mode = False
        
        if os.path.exists('emergency_mode.flag'):
            os.remove('emergency_mode.flag')
        
        print("✅ Emergency mode deactivated - normal operation restored")
    
    def send_alerts(self, alerts):
        """Send cost alerts (console for now, can add email/Slack later)"""
        for alert in alerts:
            symbol = '🚨' if alert['level'] == 'CRITICAL' else '⚠️' if alert['level'] == 'WARNING' else 'ℹ️'
            print(f"{symbol} [{alert['level']}] {alert['message']}")
    
    def get_cost_breakdown(self, hours=24):
        """Get detailed cost breakdown by service"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        time_ago = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT api_service, operation, 
                   COUNT(*) as count,
                   SUM(cost) as total_cost,
                   AVG(cost) as avg_cost
            FROM api_costs
            WHERE timestamp > ?
            GROUP BY api_service, operation
            ORDER BY total_cost DESC
        ''', (time_ago,))
        
        breakdown = []
        for row in cursor.fetchall():
            breakdown.append({
                'service': row[0],
                'operation': row[1],
                'count': row[2],
                'total_cost': round(row[3], 2),
                'avg_cost': round(row[4], 4)
            })
        
        conn.close()
        return breakdown
    
    def get_user_costs(self, limit=10):
        """Get top cost-generating users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        day_ago = datetime.now() - timedelta(days=1)
        
        cursor.execute('''
            SELECT user_id, 
                   COUNT(*) as requests,
                   SUM(cost) as total_cost
            FROM api_costs
            WHERE timestamp > ?
            GROUP BY user_id
            ORDER BY total_cost DESC
            LIMIT ?
        ''', (day_ago, limit))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'requests': row[1],
                'total_cost': round(row[2], 2)
            })
        
        conn.close()
        return users
    
    def generate_report(self):
        """Generate comprehensive cost report"""
        hourly = self.get_hourly_stats()
        daily = self.get_daily_stats()
        breakdown = self.get_cost_breakdown(hours=24)
        top_users = self.get_user_costs(limit=5)
        
        report = f"""
╔═══════════════════════════════════════════════════════════╗
║           PICLY COST MONITORING REPORT                    ║
╚═══════════════════════════════════════════════════════════╝

📊 CURRENT HOUR ({hourly['hour_start']})
   Revenue:    ${hourly['total_revenue']:>8.2f}
   Costs:      ${hourly['total_cost']:>8.2f}
   Profit:     ${hourly['profit']:>8.2f}
   Margin:     {hourly['margin']:>7.1f}%
   Requests:   {hourly['requests']:>8}
   Users:      {hourly['users']:>8}

📅 TODAY ({daily['date']})
   Revenue:    ${daily['total_revenue']:>8.2f}
   Costs:      ${daily['total_cost']:>8.2f}
   Profit:     ${daily['profit']:>8.2f}
   Margin:     {daily['margin']:>7.1f}%
   Status:     {'✅ Profitable' if daily['profitable'] else '❌ Losing Money'}

💰 COST BREAKDOWN (Last 24h)
"""
        for item in breakdown[:5]:
            report += f"   {item['service']:15} {item['operation']:20} ${item['total_cost']:>7.2f} ({item['count']} requests)\n"
        
        report += f"\n👥 TOP COST USERS (Last 24h)\n"
        for user in top_users:
            report += f"   User #{user['user_id']:>5}  ${user['total_cost']:>7.2f} ({user['requests']} requests)\n"
        
        report += "\n" + "═" * 63 + "\n"
        
        return report


# Global instance
cost_monitor = CostMonitor()


if __name__ == "__main__":
    # Test the monitoring system
    monitor = CostMonitor()
    
    # Simulate some costs
    monitor.log_api_cost(1, 'openai', 'dalle3_hd', 0.08, True)
    monitor.log_api_cost(1, 'replicate', 'gen2_video', 0.20, True)
    monitor.log_api_cost(2, 'huggingface', 'flux_image', 0.0, True)
    
    # Simulate revenue
    monitor.log_revenue(1, 9.00, 'subscription', 'Creator Monthly')
    
    # Generate report
    print(monitor.generate_report())
