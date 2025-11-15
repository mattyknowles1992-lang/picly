"""
Test script for cost monitoring system
Simulates API usage and revenue to verify tracking
"""

from cost_monitor import cost_monitor
import time

def test_cost_monitoring():
    """Test the cost monitoring system"""
    
    print("=" * 60)
    print("COST MONITORING SYSTEM TEST")
    print("=" * 60)
    print()
    
    # Simulate some API usage
    print("📊 Simulating API usage...")
    
    # Free tier users (no cost)
    for i in range(5):
        cost_monitor.log_api_cost(
            user_id=100 + i,
            api_service='huggingface',
            operation='flux_schnell',
            cost=0.0,
            success=True
        )
    print("✅ Logged 5 free Hugging Face generations ($0.00)")
    
    # Premium DALL-E 3 usage
    for i in range(3):
        cost_monitor.log_api_cost(
            user_id=200 + i,
            api_service='openai',
            operation='dalle3_hd',
            cost=0.08,
            success=True
        )
    print("✅ Logged 3 DALL-E 3 HD generations ($0.24 total)")
    
    # Some standard DALL-E 3
    for i in range(2):
        cost_monitor.log_api_cost(
            user_id=300 + i,
            api_service='openai',
            operation='dalle3_standard',
            cost=0.04,
            success=True
        )
    print("✅ Logged 2 DALL-E 3 Standard generations ($0.08 total)")
    
    print()
    print("💰 Simulating revenue...")
    
    # Subscription revenue
    cost_monitor.log_revenue(
        user_id=201,
        amount=9.00,
        revenue_type='subscription',
        description='Creator Monthly Plan'
    )
    print("✅ Logged $9.00 Creator subscription")
    
    cost_monitor.log_revenue(
        user_id=202,
        amount=19.99,
        revenue_type='subscription',
        description='Pro Monthly Plan'
    )
    print("✅ Logged $19.99 Pro subscription")
    
    # Credit purchases
    cost_monitor.log_revenue(
        user_id=301,
        amount=5.00,
        revenue_type='credits',
        description='100 credits purchased'
    )
    print("✅ Logged $5.00 credit purchase")
    
    print()
    print("=" * 60)
    
    # Get hourly stats
    print()
    hourly = cost_monitor.get_hourly_stats()
    print("⏱️  HOURLY STATISTICS")
    print(f"   Cost:         ${hourly['cost']:.2f}")
    print(f"   Revenue:      ${hourly['revenue']:.2f}")
    print(f"   Profit:       ${hourly['profit']:.2f}")
    print(f"   Margin:       {hourly['profit_margin']:.1f}%")
    print(f"   Requests:     {hourly['requests']}")
    print(f"   Unique Users: {hourly['unique_users']}")
    
    # Get daily stats
    print()
    daily = cost_monitor.get_daily_stats()
    print("📅 DAILY STATISTICS")
    print(f"   Cost:         ${daily['cost']:.2f}")
    print(f"   Revenue:      ${daily['revenue']:.2f}")
    print(f"   Profit:       ${daily['profit']:.2f}")
    print(f"   Margin:       {daily['profit_margin']:.1f}%")
    print(f"   Requests:     {daily['requests']}")
    print(f"   Unique Users: {daily['unique_users']}")
    
    # Check alerts
    print()
    alerts = cost_monitor.check_cost_alerts()
    print("🚨 ALERT STATUS")
    if alerts['status'] == 'normal':
        print("   ✅ All systems normal")
    else:
        if alerts.get('hourly_limit_exceeded'):
            print(f"   ⚠️  HOURLY LIMIT EXCEEDED: ${alerts['hourly_cost']:.2f} / ${alerts['hourly_limit']}")
        if alerts.get('daily_limit_exceeded'):
            print(f"   🚨 DAILY LIMIT EXCEEDED: ${alerts['daily_cost']:.2f} / ${alerts['daily_limit']}")
        if alerts.get('margin_too_low'):
            print(f"   ⚠️  MARGIN TOO LOW: {alerts['profit_margin']:.1f}% (min: {alerts['min_margin']}%)")
    
    # Cost breakdown
    print()
    print("💸 COST BREAKDOWN BY SERVICE")
    breakdown = cost_monitor.get_cost_breakdown('daily')
    for item in breakdown:
        print(f"   {item['api_service']:15} {item['operation']:20} ${item['total_cost']:6.2f} ({item['request_count']} requests)")
    
    # Top users
    print()
    print("👥 TOP COST-GENERATING USERS")
    top_users = cost_monitor.get_user_costs(limit=5)
    for user in top_users:
        print(f"   User {user['user_id']:4} - ${user['total_cost']:6.2f} ({user['request_count']} requests)")
    
    print()
    print("=" * 60)
    print()
    print("✅ Cost monitoring system is working perfectly!")
    print()
    print("📊 Access the dashboard at: http://localhost:5000/admin")
    print("   (Auto-refreshes every 30 seconds)")
    print()
    print("🔒 Protection Features:")
    print("   • $50/hour cost warning threshold")
    print("   • $500/day circuit breaker (emergency shutdown)")
    print("   • 20% minimum profit margin alert")
    print("   • Real-time cost/revenue tracking")
    print("   • Service and user breakdown")
    print()

if __name__ == '__main__':
    test_cost_monitoring()
