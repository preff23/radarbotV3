"""Client for interacting with CorpBonds.ru API."""

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BondData:
    isin: str
    bond_short_name: str
    bond_full_name: str
    issuer_id: int
    issuer_name: str


@dataclass
class IssuerData:
    id: int
    name: str


class CorpBondsClient:
    
    def __init__(self):
        self.base_url = "https://corpbonds.ru"
        self.session = None
    
    async def __aenter__(self):
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=30))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_all_bonds(self) -> List[BondData]:
        try:
            url = f"{self.base_url}/screener/quickdata"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to get bonds data: {response.status}")
                    return []
                
                data = await response.json()
                
                bonds = []
                if 'bonds' in data:
                    for bond_info in data['bonds']:
                        bond = BondData(
                            isin=bond_info.get('isin', ''),
                            bond_short_name=bond_info.get('bondShortName', ''),
                            bond_full_name=bond_info.get('bondFullName', ''),
                            issuer_id=bond_info.get('issuerId', 0),
                            issuer_name=bond_info.get('issuerName', '')
                        )
                        bonds.append(bond)
                
                logger.info(f"Retrieved {len(bonds)} bonds from CorpBonds.ru")
                return bonds
                
        except Exception as e:
            logger.error(f"Failed to get bonds data: {e}")
            return []
    
    async def get_all_issuers(self) -> List[IssuerData]:
        try:
            url = f"{self.base_url}/screener/quickdata"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to get issuers data: {response.status}")
                    return []
                
                data = await response.json()
                
                issuers = []
                if 'issuers' in data:
                    for issuer_info in data['issuers']:
                        issuer = IssuerData(
                            id=issuer_info.get('id', 0),
                            name=issuer_info.get('name', '')
                        )
                        issuers.append(issuer)
                
                logger.info(f"Retrieved {len(issuers)} issuers from CorpBonds.ru")
                return issuers
                
        except Exception as e:
            logger.error(f"Failed to get issuers data: {e}")
            return []
    
    async def get_bond_by_isin(self, isin: str) -> Optional[BondData]:
        bonds = await self.get_all_bonds()
        
        for bond in bonds:
            if bond.isin == isin:
                return bond
        
        return None
    
    async def get_bonds_by_issuer(self, issuer_name: str) -> List[BondData]:
        bonds = await self.get_all_bonds()
        
        issuer_bonds = []
        for bond in bonds:
            if bond.issuer_name and issuer_name.lower() in bond.issuer_name.lower():
                issuer_bonds.append(bond)
        
        return issuer_bonds
    
    def create_isin_to_issuer_mapping(self, bonds: List[BondData]) -> Dict[str, str]:
        mapping = {}
        
        for bond in bonds:
            mapping[bond.isin] = bond.issuer_name
        
        return mapping
    
    def create_issuer_to_ticker_mapping(self, issuers: List[IssuerData]) -> Dict[str, str]:
        mapping = {}
        
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
        
        for issuer in issuers:
            if issuer.name in ticker_mapping:
                mapping[issuer.name] = ticker_mapping[issuer.name]
        
        return mapping


async def test_corpbonds_client():
    print("Testing CorpBonds.ru Client...")
    
    async with CorpBondsClient() as client:
        print("\n--- Getting all bonds ---")
        bonds = await client.get_all_bonds()
        print(f"Retrieved {len(bonds)} bonds")
        
        for i, bond in enumerate(bonds[:5]):
            print(f"{i+1}. {bond.bond_short_name} ({bond.isin}) - {bond.issuer_name}")
        
        print("\n--- Getting all issuers ---")
        issuers = await client.get_all_issuers()
        print(f"Retrieved {len(issuers)} issuers")
        
        for i, issuer in enumerate(issuers[:10]):
            print(f"{i+1}. {issuer.name} (ID: {issuer.id})")
        
        print("\n--- Creating ISIN to issuer mapping ---")
        isin_mapping = client.create_isin_to_issuer_mapping(bonds)
        print(f"Created mapping for {len(isin_mapping)} bonds")
        
        sample_isins = list(isin_mapping.keys())[:5]
        for isin in sample_isins:
            print(f"{isin} -> {isin_mapping[isin]}")
        
        print("\n--- Creating issuer to ticker mapping ---")
        ticker_mapping = client.create_issuer_to_ticker_mapping(issuers)
        print(f"Created mapping for {len(ticker_mapping)} issuers")
        
        for issuer_name, ticker in list(ticker_mapping.items())[:5]:
            print(f"{issuer_name} -> {ticker}")
        
        print("\n--- Testing bond lookup by ISIN ---")
        if bonds:
            test_isin = bonds[0].isin
            bond = await client.get_bond_by_isin(test_isin)
            if bond:
                print(f"Found bond: {bond.bond_short_name} - {bond.issuer_name}")
            else:
                print("Bond not found")
        
        print("\n--- Testing bonds by issuer ---")
        sber_bonds = await client.get_bonds_by_issuer("Сбербанк")
        print(f"Found {len(sber_bonds)} Sberbank bonds")
        
        for bond in sber_bonds[:3]:
            print(f"- {bond.bond_short_name} ({bond.isin})")


if __name__ == "__main__":
    asyncio.run(test_corpbonds_client())