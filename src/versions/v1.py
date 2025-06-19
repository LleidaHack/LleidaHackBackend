from fastapi import APIRouter

from src.impl.Article import router_v1 as Article
from src.impl.ArticleType import router_v1 as ArticleType
from src.impl.Authentication import router_v1 as Authentication
from src.impl.Company import router_v1 as Company
from src.impl.CompanyUser import router_v1 as CompanyUser
from src.impl.Event import router_v1 as Event
from src.impl.Hacker import router_v1 as Hacker
from src.impl.HackerGroup import router_v1 as HackerGroup
from src.impl.LleidaHacker import router_v1 as LleidaHacker
from src.impl.LleidaHackerGroup import router_v1 as LleidaHackerGroup
from src.impl.Meal import router_v1 as Meal
from src.impl.User import router_v1 as User
from src.impl.UserConfig import router_v1 as UserConfig

router = APIRouter(prefix="/v1")

router.include_router(User.router)
router.include_router(HackerGroup.router)
router.include_router(LleidaHacker.router)
router.include_router(LleidaHackerGroup.router)
router.include_router(Company.router)
router.include_router(CompanyUser.router)
router.include_router(Meal.router)
router.include_router(Event.router)
router.include_router(Authentication.router)
router.include_router(Hacker.router)
router.include_router(UserConfig.router)
router.include_router(Article.router)
router.include_router(ArticleType.router)
