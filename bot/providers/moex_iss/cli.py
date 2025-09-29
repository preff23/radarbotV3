import asyncio
import sys
import argparse
from typing import Optional
from bot.providers.moex_iss.client import MOEXISSClient
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_search(query: str):
    async with MOEXISSClient() as client:
        print(f"Searching for: {query}")
        results = await client.search_securities(query, limit=10)
        
        if not results:
            print("No results found")
            return
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.shortname} ({result.secid}) - {result.name}")
            if result.isin:
                print(f"   ISIN: {result.isin}")
            if result.type:
                print(f"   Type: {result.type}")
            print()


async def test_share(secid: str):
    async with MOEXISSClient() as client:
        print(f"Getting share data for: {secid}")
        
        info = await client.get_share_info(secid)
        if info:
            print("Security Info:")
            print(f"  SECID: {info.secid}")
            print(f"  Short Name: {info.shortname}")
            print(f"  Name: {info.name}")
            if info.isin:
                print(f"  ISIN: {info.isin}")
            if info.type:
                print(f"  Type: {info.type}")
            print()
        
        marketdata = await client.get_share_marketdata(secid)
        if marketdata:
            print("Market Data:")
            print(f"  Last Price: {marketdata.last}")
            print(f"  Change: {marketdata.change_day_pct}%")
            print(f"  Trading Status: {marketdata.trading_status}")
            print(f"  Currency: {marketdata.currency}")
            if marketdata.sector:
                print(f"  Sector: {marketdata.sector}")
        else:
            print("No market data available")


async def test_bond(secid: str):
    async with MOEXISSClient() as client:
        print(f"Getting bond data for: {secid}")
        
        info = await client.get_bond_info(secid)
        if info:
            print("Security Info:")
            print(f"  SECID: {info.secid}")
            print(f"  Short Name: {info.shortname}")
            print(f"  Name: {info.name}")
            if info.isin:
                print(f"  ISIN: {info.isin}")
            if info.type:
                print(f"  Type: {info.type}")
            print()
        
        marketdata = await client.get_bond_marketdata(secid)
        if marketdata:
            print("Market Data:")
            print(f"  Last Price: {marketdata.last}")
            print(f"  Change: {marketdata.change_day_pct}%")
            print(f"  Trading Status: {marketdata.trading_status}")
            print(f"  YTM: {marketdata.ytm}%")
            print(f"  Duration: {marketdata.duration}")
            print(f"  ACI: {marketdata.aci}")
            print(f"  Currency: {marketdata.currency}")
        else:
            print("No market data available")


async def test_calendar(secid: str):
    async with MOEXISSClient() as client:
        print(f"Getting bond calendar for: {secid}")
        
        calendar = await client.get_bond_calendar(secid, days_ahead=30)
        if not calendar:
            print("No calendar data available")
            return
        
        print(f"Calendar for {secid} (next 30 days):")
        
        if calendar.coupons:
            print("\nCoupons:")
            for coupon in calendar.coupons:
                print(f"  {coupon.coupon_date.strftime('%Y-%m-%d')}: {coupon.coupon_value}")
        
        if calendar.amortizations:
            print("\nAmortizations:")
            for amort in calendar.amortizations:
                print(f"  {amort.amort_date.strftime('%Y-%m-%d')}: {amort.amort_value}")
        
        if not calendar.coupons and not calendar.amortizations:
            print("No upcoming events in the next 30 days")


async def main():
    parser = argparse.ArgumentParser(description="MOEX ISS CLI tester")
    parser.add_argument("command", choices=["search", "share", "bond", "calendar"])
    parser.add_argument("identifier", help="Search query, SECID, or ISIN")
    
    args = parser.parse_args()
    
    try:
        if args.command == "search":
            await test_search(args.identifier)
        elif args.command == "share":
            await test_share(args.identifier)
        elif args.command == "bond":
            await test_bond(args.identifier)
        elif args.command == "calendar":
            await test_calendar(args.identifier)
    except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())