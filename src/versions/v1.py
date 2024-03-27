from fastapi import APIRouter
from src.impl.User import router as User
from src.impl.HackerGroup import router as HackerGroup
from src.impl.LleidaHacker import router as LleidaHacker
from src.impl.LleidaHackerGroup import router as LleidaHackerGroup
from src.impl.Company import router as Company
from src.impl.CompanyUser import router as CompanyUser
from src.impl.Meal import router as Meal
from src.impl.Event import router as Event
from src.impl.Authentication import router as Authentication
from src.impl.Hacker import router as Hacker
from src.impl.UserConfig import router_v1 as UserConfig
from src.impl.Hacker import router as Hacker

router = APIRouter(prefix="/v1",
                   # tags=['v1']
                   )

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
router.include_router(Hacker.router)
