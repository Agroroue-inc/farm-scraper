from .serres_quebec import SerresQuebecScraper
from .cggd_directory import CGGDDirectoryScraper
from .cfia_inspection import CFIAInspectionScraper
from .cea_alliance import CEAAllianceScraper
from .apmquebec import APMQuebecScraper
from .pages_jaunes import PagesJaunesScraper
from .origa import OrigaScraper
from .fermier_famille import FermierFamilleScraper

ALL_SCRAPERS = {
    "serres_quebec": SerresQuebecScraper,
    "cggd": CGGDDirectoryScraper,
    "cfia": CFIAInspectionScraper,
    "cea_alliance": CEAAllianceScraper,
    "apmquebec": APMQuebecScraper,
    "pages_jaunes": PagesJaunesScraper,
    "origa": OrigaScraper,
    "fermier_famille": FermierFamilleScraper,
}
