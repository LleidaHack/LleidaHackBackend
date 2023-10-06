from models.User import User as ModelUser
from models.Hacker import Hacker as ModelHacker
from models.Hacker import HackerGroup as ModelHackerGroup
from models.LleidaHacker import LleidaHacker as ModelLleidaHacker
from models.Company import CompanyUser as ModelCompanyUser


def user_show_private(user: ModelUser):
    # user.password
    # user.rest_password_token
    # user.refresh_token
    user.email
    user.telephone
    user.address
    user.shirt_size
    user.code
    user.food_restrictions


def hacker_show_private(hacker: ModelHacker):
    user_show_private(hacker)
    hacker.cv
    hacker.banned
    hacker.studies
    hacker.study_center
    hacker.location
    hacker.how_did_you_meet_us


def lleidahacker_show_private(lleidahacker: ModelLleidaHacker):
    user_show_private(lleidahacker)
    lleidahacker.role
    lleidahacker.nif
    lleidahacker.accepted
    lleidahacker.rejected


def companyuser_show_private(company: ModelCompanyUser):
    user_show_private(company)
    company.active
    company.role
    company.accepted
    company.rejected


def hackergroup_show_private(hackergroup: ModelHackerGroup):
    hackergroup.code
