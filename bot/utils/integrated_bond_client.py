"""Integrated bond data client using optimal strategy: CorpBonds.ru -> T-Bank -> MOEX ISS."""

import asyncio
import aiohttp
import ssl
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class BondData:
    isin: str
    name: str
    issuer_name: str
    issuer_id: Optional[int] = None
    
    price: Optional[float] = None
    yield_to_maturity: Optional[float] = None
    duration: Optional[float] = None
    volume: Optional[float] = None
    face_value: Optional[float] = None
    
    sector: Optional[str] = None
    security_type: Optional[str] = None
    
    corpbonds_found: bool = False
    tbank_found: bool = False
    moex_found: bool = False
    
    last_updated: Optional[datetime] = None
    confidence: str = "low"
    
    # Дополнительные атрибуты для совместимости с IntegratedSnapshot
    last_price: Optional[float] = None
    change_day_pct: Optional[float] = None
    currency: str = "RUB"
    ticker: Optional[str] = None
    secid: Optional[str] = None
    trading_status: str = "NormalTrading"
    shortname: Optional[str] = None
    board: str = "TQCB"
    aci: float = 0.0
    ytm: Optional[float] = None
    next_coupon_date: Optional[datetime] = None
    provider: str = "integrated"
    maturity_date: Optional[datetime] = None
    coupon_rate: float = 0.0
    coupon_frequency: int = 0
    issue_date: Optional[datetime] = None
    issue_size: float = 0.0
    rating: Optional[str] = None
    rating_agency: Optional[str] = None


class IntegratedBondClient:
    
    def __init__(self):
        self.corpbonds_url = "https://corpbonds.ru/screener/quickdata"
        self.tbank_url = "https://api.tbank.ru/api/v1/bonds/search"
        self.moex_url = "https://iss.moex.com/iss"
        
        self.session = None
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)
        
        self.corpbonds_bonds = []
        self.corpbonds_issuers = []
        self.isin_to_issuer_mapping = {}
        self.issuer_to_ticker_mapping = {}
    
    async def __aenter__(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=30))
        
        await self._load_corpbonds_data()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _load_corpbonds_data(self):
        try:
            async with self.session.get(self.corpbonds_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'bonds' in data:
                        self.corpbonds_bonds = data['bonds']
                        logger.info(f"Loaded {len(self.corpbonds_bonds)} bonds from CorpBonds.ru")
                    
                    if 'issuers' in data:
                        self.corpbonds_issuers = data['issuers']
                        logger.info(f"Loaded {len(self.corpbonds_issuers)} issuers from CorpBonds.ru")
                    
                    self._create_mappings()
                    
        except Exception as e:
            logger.error(f"Failed to load CorpBonds.ru data: {e}")
    
    def _create_mappings(self):
        self.isin_to_issuer_mapping = {}
        for bond in self.corpbonds_bonds:
            if bond.get('isin') and bond.get('issuerName'):
                self.isin_to_issuer_mapping[bond['isin']] = bond['issuerName']
        
        ticker_mapping = {
            'Сбербанк России': 'SBER',
            'Газпром': 'GAZP',
            'ЛУКОЙЛ': 'LKOH',
            'Роснефть НК': 'ROSN',
            'Норильский Никель ГМК': 'GMKN',
            'МТС': 'MTSS',
            'МегаФон': 'MFON',
            'Яндекс МКПАО': 'YNDX',
            'Аэрофлот': 'AFLT',
            'Магнит': 'MGNT',
            'Полюс': 'PLZL',
            'Северсталь': 'CHMF',
            'Новатэк': 'NVTK',
            'ФосАгро': 'PHOR',
            'Татнефтехим': 'TATN',
            'НЛМК': 'NLMK',
            'СИБУР Холдинг': 'SIBU',
            'РусГидро': 'HYDR',
            'Ростелеком': 'RTKM',
            'КАМАЗ': 'KMAZ',
            'ВымпелКом': 'VKCO',
            'Озон': 'OZON',
            'Т1': 'TCSG',
            'АО "ТБанк"': 'TINK',
            'АО "АЛЬФА-БАНК"': 'ALFA',
            'Банк ВТБ': 'VTBR',
            'АО "Россельхозбанк"': 'RUSB',
            'ПАО ПСБ': 'PSBR',
            'ПАО "Совкомбанк"': 'SVCB',
            'ПАО "МОСКОВСКИЙ КРЕДИТНЫЙ БАНК"': 'MKB',
            'АО "МСП Банк"': 'MSPB',
            'АО "Банк ДОМ.РФ"': 'DOMR',
            'АО "ЯНДЕКС БАНК"': 'YNDX',
            'АО "ТОРГОВЫЙ ДОМ "ПЕРЕКРЕСТОК""': 'X5R',
            'АО "ЕВРАЗ НТМК"': 'EVRAZ',
            'АО "СУЭК"': 'SUEK',
            'МКООО "ЭН+ ХОЛДИНГ"': 'ENPG',
            'МКПАО "ВК"': 'VKCO',
            'ПАО «ИВА»': 'IVAN',
            'ПАО "РОСИНТЕР"': 'ROSN',
            'Акционерное общество "Акционерный Банк "РОССИЯ""': 'RUSB'
        }
        
        self.issuer_to_ticker_mapping = {}
        for issuer in self.corpbonds_issuers:
            if issuer.get('name') in ticker_mapping:
                self.issuer_to_ticker_mapping[issuer['name']] = ticker_mapping[issuer['name']]
    
    async def get_bond_data(self, isin: str, ticker: str = None) -> Optional[BondData]:
        try:
            cache_key = f"bond_{isin}_{ticker or ''}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if datetime.now() - cached_time < self.cache_ttl:
                    logger.info(f"Using cached data for {isin}")
                    return cached_data
            
            bond_data = None
            if isin:
                bond_data = await self._get_corpbonds_data(isin)
            
            if not bond_data and ticker:
                bond_data = await self._get_moex_data_by_ticker(ticker)
            
            # Если нет данных от CorpBonds.ru и MOEX, создаем базовый объект
            if not bond_data:
                bond_data = BondData(
                    isin=isin,
                    name=isin,
                    issuer_name=isin,
                    security_type="bond"
                )
            
            # Всегда пытаемся обогатить данными T-Bank
            await self._enrich_with_tbank_data(bond_data, isin or ticker)
            
            # Всегда пытаемся обогатить данными MOEX
            await self._enrich_with_moex_data(bond_data, isin or ticker)
            
            # Синхронизируем атрибуты для совместимости
            self._sync_attributes(bond_data)
            
            if bond_data:
                bond_data.last_updated = datetime.now()
                self.cache[cache_key] = (bond_data, datetime.now())
            
            return bond_data
            
        except Exception as e:
            logger.error(f"Failed to get bond data for {isin}/{ticker}: {e}")
            return None
    
    def _sync_attributes(self, bond_data: BondData):
        """Синхронизирует атрибуты для совместимости с IntegratedSnapshot"""
        if bond_data:
            # Синхронизируем основные атрибуты
            bond_data.last_price = bond_data.price
            bond_data.ytm = bond_data.yield_to_maturity
            bond_data.ticker = bond_data.isin
            bond_data.secid = bond_data.isin
            bond_data.shortname = bond_data.name
            
            # Устанавливаем значения по умолчанию если не заданы
            if bond_data.change_day_pct is None:
                bond_data.change_day_pct = 0.0
    
    async def _get_corpbonds_data(self, isin: str) -> Optional[BondData]:
        try:
            bond_info = None
            for bond in self.corpbonds_bonds:
                if bond.get('isin') == isin:
                    bond_info = bond
                    break
            
            if not bond_info:
                logger.warning(f"Bond {isin} not found in CorpBonds.ru")
                return None
            
            bond_data = BondData(
                isin=isin,
                name=bond_info.get('bondShortName', ''),
                issuer_name=bond_info.get('issuerName', ''),
                issuer_id=bond_info.get('issuerId'),
                corpbonds_found=True,
                confidence="medium"
            )
            
            logger.info(f"Found bond {isin} in CorpBonds.ru: {bond_data.name} - {bond_data.issuer_name}")
            return bond_data
            
        except Exception as e:
            logger.error(f"Failed to get CorpBonds.ru data for {isin}: {e}")
            return None
    
    async def _get_moex_data_by_ticker(self, ticker: str) -> Optional[BondData]:
        try:
            logger.info(f"Searching bond by ticker {ticker} on MOEX...")
            
            from bot.providers.moex_iss.client import MOEXISSClient
            
            async with MOEXISSClient() as moex_client:
                bond_info = await moex_client.get_bond_info(ticker)
                
                if bond_info:
                    bond_data = BondData(
                        isin=getattr(bond_info, 'isin', None) or ticker,
                        name=getattr(bond_info, 'name', None) or ticker,
                        issuer_name=getattr(bond_info, 'issuer_name', None) or "Unknown",
                        moex_found=True,
                        confidence="medium"
                    )
                    
                    logger.info(f"Found bond {ticker} on MOEX: {bond_data.name}")
                    return bond_data
                else:
                    logger.warning(f"Bond {ticker} not found on MOEX")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to search MOEX for ticker {ticker}: {e}")
            return None
    
    async def _enrich_with_tbank_data(self, bond_data: BondData, identifier: str):
        try:
            tbank_data = await self._search_tbank(identifier)
            
            if tbank_data:
                bond_data.price = tbank_data.get('price')
                bond_data.security_type = tbank_data.get('instrument_type')
                bond_data.tbank_found = True
                bond_data.confidence = "high"
                
                if tbank_data.get('name') and not bond_data.name:
                    bond_data.name = tbank_data.get('name')
                
                logger.info(f"Enriched {identifier} with T-Bank data: price={bond_data.price}, type={bond_data.security_type}")
            else:
                logger.warning(f"No T-Bank data found for {identifier}")
                
        except Exception as e:
            logger.error(f"Failed to enrich with T-Bank data for {identifier}: {e}")
    
    async def _enrich_with_moex_data(self, bond_data: BondData, isin: str):
        try:
            moex_data = await self._get_moex_data(isin)
            
            if moex_data:
                if not bond_data.price or moex_data.get('price'):
                    bond_data.price = moex_data.get('price')
                
                bond_data.yield_to_maturity = moex_data.get('ytm')
                bond_data.duration = moex_data.get('duration')
                bond_data.volume = moex_data.get('volume')
                bond_data.face_value = moex_data.get('face_value')
                bond_data.moex_found = True
                bond_data.confidence = "very_high"
                
                if moex_data.get('shortname') and not bond_data.name:
                    bond_data.name = moex_data.get('shortname')
                
                logger.info(f"Enriched {isin} with MOEX data: price={bond_data.price}, ytm={bond_data.yield_to_maturity}, duration={bond_data.duration}")
            else:
                logger.warning(f"No MOEX data found for {isin}")
                
        except Exception as e:
            logger.error(f"Failed to enrich with MOEX data for {isin}: {e}")
    
    async def _search_tbank(self, isin: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Searching {isin} in T-Bank...")
            
            from bot.providers.tbank_rest import TBankRestClient
            
            async with TBankRestClient() as tbank_client:
                instruments = await tbank_client.find_instrument(isin)
                
                if instruments:
                    instrument = instruments[0]
                    
                    prices = await tbank_client.get_last_prices([instrument.figi])
                    
                    price_data = None
                    if prices:
                        price_data = prices[0]
                    
                    return {
                        'figi': instrument.figi,
                        'ticker': instrument.ticker,
                        'name': instrument.name,
                        'isin': instrument.isin,
                        'instrument_type': instrument.instrument_type,
                        'currency': instrument.currency,
                        'price': price_data.price if price_data else None,
                        'price_currency': instrument.currency,
                        'last_update': price_data.time if price_data else None
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to search T-Bank for {isin}: {e}")
            return None
    
    async def _get_moex_data(self, isin: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Getting {isin} from MOEX ISS...")
            
            from bot.providers.moex_iss.client import MOEXISSClient
            
            async with MOEXISSClient() as moex_client:
                search_results = await moex_client.search_securities(isin)
                
                if search_results:
                    result = search_results[0]
                    
                    bond_snapshot = await moex_client.get_bond_marketdata(result.secid)
                    
                    if bond_snapshot:
                        return {
                            'secid': bond_snapshot.secid,
                            'shortname': bond_snapshot.shortname,
                            'price': bond_snapshot.last,
                            'change_day_pct': bond_snapshot.change_day_pct,
                            'trading_status': bond_snapshot.trading_status,
                            'ytm': bond_snapshot.ytm,
                            'duration': bond_snapshot.duration,
                            'aci': bond_snapshot.aci,
                            'currency': bond_snapshot.currency,
                            'board': bond_snapshot.board,
                            'face_value': bond_snapshot.face_value
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get MOEX data for {isin}: {e}")
            return None
    
    async def get_bonds_by_issuer(self, issuer_name: str) -> List[BondData]:
        try:
            bonds = []
            
            for bond_info in self.corpbonds_bonds:
                if (bond_info.get('issuerName') and 
                    issuer_name.lower() in bond_info['issuerName'].lower()):
                    
                    isin = bond_info.get('isin')
                    if isin:
                        bond_data = await self.get_bond_data(isin)
                        if bond_data:
                            bonds.append(bond_data)
            
            logger.info(f"Found {len(bonds)} bonds for issuer {issuer_name}")
            return bonds
            
        except Exception as e:
            logger.error(f"Failed to get bonds by issuer {issuer_name}: {e}")
            return []
    
    def get_issuer_by_isin(self, isin: str) -> Optional[str]:
        return self.isin_to_issuer_mapping.get(isin)
    
    def get_ticker_by_issuer(self, issuer_name: str) -> Optional[str]:
        return self.issuer_to_ticker_mapping.get(issuer_name)
    
    def format_bond_summary(self, bond_data: BondData) -> str:
        if not bond_data:
            return "Bond data not available"
        
        summary = f"📊 {bond_data.name} ({bond_data.isin})\n"
        summary += f"🏢 Эмитент: {bond_data.issuer_name}\n"
        
        if bond_data.price:
            summary += f"💰 Цена: {bond_data.price:.2f} ₽\n"
        if bond_data.yield_to_maturity:
            summary += f"📈 Доходность: {bond_data.yield_to_maturity:.2f}%\n"
        if bond_data.sector:
            summary += f"🏭 Отрасль: {bond_data.sector}\n"
        
        sources = []
        if bond_data.corpbonds_found:
            sources.append("CorpBonds.ru")
        if bond_data.tbank_found:
            sources.append("T-Bank")
        if bond_data.moex_found:
            sources.append("MOEX ISS")
        
        summary += f"📡 Источники: {', '.join(sources)}\n"
        summary += f"🎯 Уверенность: {bond_data.confidence}"
        
        return summary


async def test_integrated_client():
    print("Testing Integrated Bond Client...")
    
    async with IntegratedBondClient() as client:
        test_isin = "RU000A0NR9S6"
        
        print(f"\n--- Testing bond: {test_isin} ---")
        
        bond_data = await client.get_bond_data(test_isin)
        
        if bond_data:
            print("✅ Bond data retrieved:")
            print(client.format_bond_summary(bond_data))
        else:
            print("❌ No bond data available")
        
        print(f"\n--- Testing issuer lookup ---")
        issuer = client.get_issuer_by_isin(test_isin)
        print(f"ISIN {test_isin} → Issuer: {issuer}")
        
        if issuer:
            ticker = client.get_ticker_by_issuer(issuer)
            print(f"Issuer {issuer} → Ticker: {ticker}")
        
        print(f"\n--- Testing bonds by issuer ---")
        sber_bonds = await client.get_bonds_by_issuer("Сбербанк")
        print(f"Found {len(sber_bonds)} Sberbank bonds")
        
        for i, bond in enumerate(sber_bonds[:3]):
            print(f"{i+1}. {bond.name} ({bond.isin})")


if __name__ == "__main__":
    asyncio.run(test_integrated_client())