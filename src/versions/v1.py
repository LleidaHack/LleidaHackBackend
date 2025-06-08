from fastapi import APIRouter

from src.impl.Article import router_v1 as article_router
from src.impl.ArticleType import router_v1 as article_type_router
from src.impl.Authentication import router_v1 as authentication_router
from src.impl.Company import router_v1 as company_router
from src.impl.CompanyUser import router_v1 as company_user_router
from src.impl.Event import router_v1 as event_router
from src.impl.Hacker import router_v1 as hacker_router
from src.impl.HackerGroup import router_v1 as hacker_group_router
from src.impl.LleidaHacker import router_v1 as lleida_hacker_router
from src.impl.LleidaHackerGroup import router_v1 as lleida_hacker_group_router
from src.impl.Meal import router_v1 as meal_router
from src.impl.User import router_v1 as user_router
from src.impl.UserConfig import router_v1 as user_config_router

router = APIRouter(prefix='/v1')

router.include_router(user_router.router)
router.include_router(hacker_group_router.router)
router.include_router(lleida_hacker_router.router)
router.include_router(lleida_hacker_group_router.router)
router.include_router(company_router.router)
router.include_router(company_user_router.router)
router.include_router(meal_router.router)
router.include_router(event_router.router)
router.include_router(authentication_router.router)
router.include_router(hacker_router.router)
router.include_router(user_config_router.router)
router.include_router(article_router.router)
router.include_router(article_type_router.router)
