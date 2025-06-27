import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# --- Tier Data Definition ---
# This data is derived from the provided JSON-like structure.
# It defines the targets for different departments and types.
tier_data_list = [
    {"Id": 1, "Department": "ABCL", "Type": "A", "Name": "Showup Range A", "TotalTarget": 8, "DailyTarget": 0.4, "Range": "8 -", "NewRep": 4, "AdjustedTarget": 0, "PayoutPerMetric": 4000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 2, "Department": "ABCL", "Type": "B", "Name": "Showup Range B", "TotalTarget": 6, "DailyTarget": 0.3, "Range": "6 - 7", "NewRep": 3, "AdjustedTarget": 0, "PayoutPerMetric": 3000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 3, "Department": "ABCL", "Type": "C", "Name": "Showup Range C", "TotalTarget": 4, "DailyTarget": 0.2, "Range": "4 - 5", "NewRep": 2, "AdjustedTarget": 0, "PayoutPerMetric": 2000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 4, "Department": "ABCL", "Type": "Opportunity", "Name": "Opportunity Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per opportunity as AE", "Action": 0},
    {"Id": 5, "Department": "LinkedIn Outreach Specialist", "Type": "A", "Name": "Showup Range A", "TotalTarget": 6, "DailyTarget": 0.3, "Range": "6 -", "NewRep": 4, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 6, "Department": "LinkedIn Outreach Specialist", "Type": "B", "Name": "Showup Range B", "TotalTarget": 5, "DailyTarget": 0.2, "Range": "4 - 5", "NewRep": 3, "AdjustedTarget": 0, "PayoutPerMetric": 4000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 7, "Department": "LinkedIn Outreach Specialist", "Type": "C", "Name": "Showup Range C", "TotalTarget": 4, "DailyTarget": 0.1, "Range": "2 - 3", "NewRep": 2, "AdjustedTarget": 0, "PayoutPerMetric": 3000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 8, "Department": "LinkedIn Outreach Specialist", "Type": "Kicker", "Name": "Scheduled Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 1000, "Currency": "PKR", "Comments": "Per approved appointment scheduled", "Action": 0},
    {"Id": 9, "Department": "LinkedIn Outreach Specialist", "Type": "Closed", "Name": "Closed Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 100, "Currency": "USD", "Comments": "Paid on per closed appointment", "Action": 0},
    {"Id": 10, "Department": "ENT", "Type": "A", "Name": "Showup Range A", "TotalTarget": 6, "DailyTarget": 0, "Range": "6 -", "NewRep": 4, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0}, # Adjusted Payactiv-ENT Tier A to 6 based on example
    {"Id": 11, "Department": "ENT", "Type": "B", "Name": "Showup Range B", "TotalTarget": 5, "DailyTarget": 0, "Range": "5 - 7", "NewRep": 3, "AdjustedTarget": 0, "PayoutPerMetric": 4000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 12, "Department": "ENT", "Type": "C", "Name": "Showup Range C", "TotalTarget": 1, "DailyTarget": 0, "Range": "1 - 4", "NewRep": 1, "AdjustedTarget": 0, "PayoutPerMetric": 3000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 13, "Department": "SMB", "Type": "A", "Name": "Showup Range A", "TotalTarget": 12, "DailyTarget": 0, "Range": "12 -", "NewRep": 4, "AdjustedTarget": 0, "PayoutPerMetric": 2250, "Currency": "PKR", "Comments": "", "Action": 0}, # Adjusted Payactiv-SMB Tier A to 12
    {"Id": 14, "Department": "SMB", "Type": "B", "Name": "Showup Range B", "TotalTarget": 5, "DailyTarget": 0, "Range": "5 - 7", "NewRep": 3, "AdjustedTarget": 0, "PayoutPerMetric": 1750, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 15, "Department": "SMB", "Type": "C", "Name": "Showup Range C", "TotalTarget": 1, "DailyTarget": 0, "Range": "1 - 4", "NewRep": 1, "AdjustedTarget": 0, "PayoutPerMetric": 1250, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 16, "Department": "MM", "Type": "A", "Name": "Showup Range A", "TotalTarget": 10, "DailyTarget": 0, "Range": "10 -", "NewRep": 4, "AdjustedTarget": 0, "PayoutPerMetric": 2500, "Currency": "PKR", "Comments": "", "Action": 0}, # Adjusted Payactiv-MM Tier A to 10
    {"Id": 17, "Department": "MM", "Type": "B", "Name": "Showup Range B", "TotalTarget": 5, "DailyTarget": 0, "Range": "5 - 7", "NewRep": 3, "AdjustedTarget": 0, "PayoutPerMetric": 2000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 18, "Department": "MM", "Type": "C", "Name": "Showup Range C", "TotalTarget": 1, "DailyTarget": 0, "Range": "1 - 4", "NewRep": 1, "AdjustedTarget": 0, "PayoutPerMetric": 1500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 19, "Department": "Pureversity", "Type": "A", "Name": "Showup Range A", "TotalTarget": 10, "DailyTarget": 0.5, "Range": "10 -", "NewRep": 5, "AdjustedTarget": 0, "PayoutPerMetric": 4000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 20, "Department": "Pureversity", "Type": "B", "Name": "Showup Range B", "TotalTarget": 7, "DailyTarget": 0.35, "Range": "7 - 9", "NewRep": 4, "AdjustedTarget": 0, "PayoutPerMetric": 3000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 21, "Department": "Pureversity", "Type": "C", "Name": "Showup Range C", "TotalTarget": 5, "DailyTarget": 0.25, "Range": "5 - 6", "NewRep": 3, "AdjustedTarget": 0, "PayoutPerMetric": 2000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 22, "Department": "Payoneer", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 750, "Currency": "PKR", "Comments": "Paid on per showup in the month", "Action": 0},
    {"Id": 23, "Department": "Payoneer", "Type": "Closed", "Name": "Closed Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 750, "Currency": "PKR", "Comments": "Paid on per closed appointment", "Action": 0},
    {"Id": 24, "Department": "Payoneer-Bangladesh", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 750, "Currency": "PKR", "Comments": "Paid on per showup in the month", "Action": 0},
    {"Id": 25, "Department": "Payoneer-Bangladesh", "Type": "Closed", "Name": "Closed Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 750, "Currency": "PKR", "Comments": "Paid on per closed in the month", "Action": 0},
    {"Id": 26, "Department": "Pure VPN and Pure Dome", "Type": "A", "Name": "Showup Range A", "TotalTarget": 10, "DailyTarget": 0.5, "Range": "10 -", "NewRep": 5, "AdjustedTarget": 0, "PayoutPerMetric": 4000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 27, "Department": "Pure VPN and Pure Dome", "Type": "B", "Name": "Showup Range B", "TotalTarget": 7, "DailyTarget": 0.35, "Range": "7 - 9", "NewRep": 4, "AdjustedTarget": 0, "PayoutPerMetric": 3000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 28, "Department": "Pure VPN and Pure Dome", "Type": "C", "Name": "Showup Range C", "TotalTarget": 5, "DailyTarget": 0.25, "Range": "5 - 6", "NewRep": 3, "AdjustedTarget": 0, "PayoutPerMetric": 2000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 29, "Department": "Pure VPN and Pure Dome - PK", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 1000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 30, "Department": "Pure VPN and Pure Dome - PK", "Type": "Opportunity", "Name": "Opportunity Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 1000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 31, "Department": "Qubriux", "Type": "Appointment", "Name": "Scheduled Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 1000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 32, "Department": "Qubriux", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 33, "Department": "Mperativ", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 34, "Department": "Mperativ", "Type": "Scheduled", "Name": "Scheduled Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 35, "Department": "Mperativ", "Type": "Opportunity", "Name": "Opportunity Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 36, "Department": "Mperativ", "Type": "Closed", "Name": "Closed Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 37, "Department": "Skellam AI", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 38, "Department": "Skellam AI", "Type": "Appointment", "Name": "Scheduled Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 39, "Department": "Skellam AI", "Type": "Opportunity", "Name": "Opportunity Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 40, "Department": "Skellam AI", "Type": "Closed", "Name": "Closed Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 41, "Department": "Avibra", "Type": "A", "Name": "Showup Range A", "TotalTarget": 8, "DailyTarget": 0.4, "Range": "8 -", "NewRep": 4, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 42, "Department": "Avibra", "Type": "B", "Name": "Showup Range B", "TotalTarget": 6, "DailyTarget": 0.3, "Range": "6 - 7", "NewRep": 3, "AdjustedTarget": 0, "PayoutPerMetric": 4000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 43, "Department": "Avibra", "Type": "C", "Name": "Showup Range C", "TotalTarget": 3, "DailyTarget": 0.2, "Range": "3 - 5", "NewRep": 2, "AdjustedTarget": 0, "PayoutPerMetric": 3000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 44, "Department": "Precanto", "Type": "Appointment", "Name": "Scheduled Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per Approved Appointment", "Action": 0},
    {"Id": 45, "Department": "Precanto", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per Showup", "Action": 0},
    {"Id": 46, "Department": "Precanto", "Type": "Opportunity", "Name": "Opportunity Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per Opportunity created", "Action": 0},
    {"Id": 47, "Department": "Precanto", "Type": "Closed", "Name": "Closed Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per showup", "Action": 0}, # Note: Comment says "Per showup", might be a typo for "Per Closed"
    {"Id": 50, "Department": "FP & A Strategy Consulting", "Type": "Opportunity", "Name": "Opportunity Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per opportunity created", "Action": 0},
    {"Id": 52, "Department": "Canopy Connect", "Type": "A", "Name": "Showup Range A", "TotalTarget": 7, "DailyTarget": 0.35, "Range": "7 -", "NewRep": 4, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 53, "Department": "Canopy Connect", "Type": "B", "Name": "Showup Range B", "TotalTarget": 6, "DailyTarget": 0.25, "Range": "5 - 6", "NewRep": 3, "AdjustedTarget": 0, "PayoutPerMetric": 4000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 54, "Department": "Canopy Connect", "Type": "C", "Name": "Showup Range C", "TotalTarget": 4, "DailyTarget": 0.15, "Range": "3 - 4", "NewRep": 2, "AdjustedTarget": 0, "PayoutPerMetric": 3000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 55, "Department": "Chowmill Restaurant", "Type": "A", "Name": "Showup Range A", "TotalTarget": 20, "DailyTarget": 1, "Range": "20 -", "NewRep": 10, "AdjustedTarget": 0, "PayoutPerMetric": 2500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 56, "Department": "Chowmill Restaurant", "Type": "B", "Name": "Showup Range B", "TotalTarget": 15, "DailyTarget": 0.75, "Range": "15 - 19", "NewRep": 8, "AdjustedTarget": 0, "PayoutPerMetric": 2000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 57, "Department": "Chowmill Restaurant", "Type": "C", "Name": "Showup Range C", "TotalTarget": 10, "DailyTarget": 0.5, "Range": "10 - 14", "NewRep": 5, "AdjustedTarget": 0, "PayoutPerMetric": 1500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 58, "Department": "Chowmill", "Type": "Appointments", "Name": "Scheduled Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 2500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 59, "Department": "Chowmill", "Type": "Showup", "Name": "Shoup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 2500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 60, "Department": "Chowmill Menus", "Type": "ClosedWon", "Name": "Closed Won Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 500, "Currency": "PKR", "Comments": "500 PKR per menu", "Action": 0},
    {"Id": 61, "Department": "Chowmill Menus", "Type": "Completed", "Name": "Completed Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 700, "Currency": "PKR", "Comments": "700 PKR per menu", "Action": 0},
    {"Id": 62, "Department": "Pureversity Pakistan", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 750, "Currency": "PKR", "Comments": "Per showup", "Action": 0},
    {"Id": 63, "Department": "Genimex", "Type": "Appointment", "Name": "Scheduled Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per Approved Appointment", "Action": 0},
    {"Id": 64, "Department": "Genimex", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per Showup", "Action": 0},
    {"Id": 65, "Department": "Genimex", "Type": "Opportunity", "Name": "Opportunity Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per Opportunity created", "Action": 0},
    {"Id": 66, "Department": "Genimex", "Type": "Closed", "Name": "Closed Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per Closed Appointment", "Action": 0},
    {"Id": 67, "Department": "Workhy SDR", "Type": "Starter", "Name": "Starter Package Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 4500, "Currency": "PKR", "Comments": "For starter package", "Action": 0},
    {"Id": 68, "Department": "Workhy SDR", "Type": "Standard", "Name": "Standard Package Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 7500, "Currency": "PKR", "Comments": "For standard package", "Action": 0},
    {"Id": 69, "Department": "Workhy SDR", "Type": "FormationAddress", "Name": "Formation and Address Package", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 3500, "Currency": "PKR", "Comments": "Formation and address package together", "Action": 0},
    {"Id": 70, "Department": "Workhy SDR", "Type": "TaxPackage", "Name": "Tax Package Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "For Tax Package Only", "Action": 0},
    {"Id": 71, "Department": "Workhy SDR", "Type": "FormationAddressTax", "Name": "Formation, Address and Tax Package", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 7500, "Currency": "PKR", "Comments": "For all packages sold together", "Action": 0},
    {"Id": 75, "Department": "FP & A Strategy Consulting", "Type": "A", "Name": "Showup Range A", "TotalTarget": 12, "DailyTarget": 0.6, "Range": "12 -", "NewRep": 10, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 76, "Department": "FP & A Strategy Consulting", "Type": "B", "Name": "Showup Range B", "TotalTarget": 8, "DailyTarget": 0.4, "Range": "8 - 11", "NewRep": 8, "AdjustedTarget": 0, "PayoutPerMetric": 3500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 77, "Department": "FP & A Strategy Consulting", "Type": "C", "Name": "Showup Range C", "TotalTarget": 5, "DailyTarget": 0.25, "Range": "5 - 7", "NewRep": 4, "AdjustedTarget": 0, "PayoutPerMetric": 3000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 78, "Department": "FP & A Strategy Consulting", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 5000, "Currency": "PKR", "Comments": "Per Showup 5000", "Action": 0},
    {"Id": 79, "Department": "Payoneer Philippines", "Type": "Scheduled", "Name": "Per Appointment Scheduled", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 80, "Department": "Payoneer Philippines", "Type": "Opportunity", "Name": "Per Opportunity Created", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 81, "Department": "Payoneer Philippines", "Type": "Showup", "Name": "Per Showup", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 82, "Department": "Payoneer Philippines", "Type": "Closed", "Name": "Per Closed Appointment", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 83, "Department": "Payoneer Singapore", "Type": "Scheduled", "Name": "Per Appointment Scheduled", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 84, "Department": "Payoneer Singapore", "Type": "Opportunity", "Name": "Per Opportunity Created", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 85, "Department": "Payoneer Singapore", "Type": "Showup", "Name": "Per Showup", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 86, "Department": "Payoneer Singapore", "Type": "Closed", "Name": "Per Closed Appointment", "TotalTarget": 0, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 87, "Department": "DAGSMEJAN", "Type": "Main", "Name": "Main Tasks", "TotalTarget": 750, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 10000, "Currency": "PKR", "Comments": "Unlocked after 750 tasks performed", "Action": 0},
    {"Id": 88, "Department": "DAGSMEJAN", "Type": "Additional", "Name": "Additional Task", "TotalTarget": 100, "DailyTarget": 0, "Range": "0 - 0", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 1000, "Currency": "PKR", "Comments": "Unlocked after 100, counted in multiple of 100s", "Action": 0},
    {"Id": 89, "Department": "CP", "Type": "A", "Name": "Showup Range A", "TotalTarget": 12, "DailyTarget": 0, "Range": "12 -", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 2500, "Currency": "PKR", "Comments": "", "Action": 0}, # Adjusted Payactiv-CP Tier A to 12
    {"Id": 90, "Department": "CP", "Type": "B", "Name": "Showup Range B", "TotalTarget": 5, "DailyTarget": 0, "Range": "5 - 7", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 2000, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 91, "Department": "CP", "Type": "C", "Name": "Showup Range C", "TotalTarget": 1, "DailyTarget": 0, "Range": "1 - 4", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 1500, "Currency": "PKR", "Comments": "", "Action": 0},
    {"Id": 93, "Department": "Information Technology", "Type": "Showup", "Name": "Showup Kicker", "TotalTarget": 1, "DailyTarget": 0.05, "Range": "1 - 1", "NewRep": 0, "AdjustedTarget": 0, "PayoutPerMetric": 1, "Currency": "PKR", "Comments": "test 2", "Action": 0}
]

tier_df = pd.DataFrame(tier_data_list)
tier_df["TotalTarget"] = pd.to_numeric(tier_df["TotalTarget"], errors='coerce')
TIER_A_TYPE_NAME = "A" # Assuming "Type" "A" is always for Tier A targets

# --- Helper Functions ---
@st.cache_data # Cache known departments
def get_known_departments(df):
    return df['Department'].unique().tolist()

KNOWN_DEPARTMENTS = get_known_departments(tier_df)

def get_department_from_project(project_name):
    """Maps a project name from CSV to a department name in tier_df."""
    if not project_name or pd.isna(project_name):
        return None
    
    project_name_str = str(project_name)

    # 1. Exact match (case-insensitive for robustness)
    for dept in KNOWN_DEPARTMENTS:
        if project_name_str.lower() == dept.lower():
            return dept

    # 2. Payactiv specific mapping (case-insensitive)
    if project_name_str.lower().startswith("payactiv-"):
        parts = project_name_str.split("-")
        if len(parts) > 1:
            suffix = parts[-1]
            # Check if this suffix (e.g., ENT, SMB) is a known department
            for dept in KNOWN_DEPARTMENTS:
                if suffix.lower() == dept.lower():
                    return dept
    
    # 3. Add more custom mappings here if needed:
    # custom_map = {"Old Project Name": "New Department Name"}
    # if project_name_str in custom_map:
    #    return custom_map[project_name_str]

    # Fallback: if no specific mapping, return the original project name
    # The lookup for Tier A will then try to find this name directly in departments.
    return project_name_str


@st.cache_data
def get_tier_a_target(department_name):
    """Fetches the Tier A TotalTarget for a given department."""
    if not department_name:
        return None
    
    target_row = tier_df[
        (tier_df['Department'].str.lower() == department_name.lower()) &
        (tier_df['Type'] == TIER_A_TYPE_NAME)
    ]
    if not target_row.empty:
        return target_row.iloc[0]['TotalTarget']
    return None


st.set_page_config(layout="wide")
st.title("🏆 Achievers List Generator")

# --- Initialize Session State ---
if 'achievers_df' not in st.session_state: # Main data from uploaded CSV
    st.session_state.achievers_df = None
if 'generated_list_df' not in st.session_state: # The final list to display
    st.session_state.generated_list_df = None
if 'last_error' not in st.session_state:
    st.session_state.last_error = None
if 'last_success' not in st.session_state:
    st.session_state.last_success = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'filters' not in st.session_state: # For filtering source data
    st.session_state.filters = []

# --- File Upload ---
st.sidebar.header("1. Upload Achievement Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV file with achievement data", type=["csv"])

if uploaded_file:
    if st.session_state.uploaded_file_name != uploaded_file.name:
        try:
            df_temp = pd.read_csv(uploaded_file)
            st.session_state.achievers_df = df_temp
            st.session_state.generated_list_df = None # Reset previous result
            st.session_state.last_error = None
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.last_success = f"Successfully loaded '{uploaded_file.name}'. Configure columns and filters below."
            # Reset filters if a new file is uploaded
            st.session_state.filters = []

        except Exception as e:
            st.session_state.achievers_df = None
            st.session_state.generated_list_df = None
            st.session_state.last_error = f"Error loading CSV: {e}"
            st.session_state.last_success = None
            st.session_state.uploaded_file_name = None
else:
    if st.session_state.achievers_df is not None and uploaded_file is None: # File removed
        st.session_state.achievers_df = None
        st.session_state.generated_list_df = None
        st.session_state.last_error = None
        st.session_state.last_success = "Please upload a CSV file to begin."
        st.session_state.uploaded_file_name = None
        st.session_state.filters = []


# --- Display Messages ---
if st.session_state.last_success:
    st.sidebar.success(st.session_state.last_success)
    st.session_state.last_success = None # Clear after showing
if st.session_state.last_error:
    st.sidebar.error(st.session_state.last_error)
    st.session_state.last_error = None # Clear after showing


# --- Configuration and Display ---
if st.session_state.achievers_df is not None:
    source_df_for_achievers = st.session_state.achievers_df.copy()
    df_columns = [""] + source_df_for_achievers.columns.tolist() # Add blank option

    st.sidebar.header("2. Configure Columns")
    project_col = st.sidebar.selectbox("Select 'Project' Column", options=df_columns, key="project_col")
    sdr_col = st.sidebar.selectbox("Select 'SDR Name' Column", options=df_columns, key="sdr_col")
    achieved_col = st.sidebar.selectbox("Select 'Achieved Value' Column", options=df_columns, key="achieved_col")
    date_col_for_filtering = st.sidebar.selectbox("Select 'Date' Column (for filtering, optional)", options=df_columns, key="date_col_filter")

    # --- Source Data Filtering (adapted from pivot_tool.py) ---
    st.sidebar.header("3. Filter Source Data (Optional)")

    def add_filter():
        st.session_state.filters.append({"column": None, "operator": "==", "value": ""})

    def remove_filter(index):
        if 0 <= index < len(st.session_state.filters):
            st.session_state.filters.pop(index)

    filter_columns_options = [""] + source_df_for_achievers.columns.tolist()
    for i, f in enumerate(st.session_state.filters):
        filter_ui_cols = st.sidebar.columns([3,2,3,1])
        current_filter_col_val = f["column"]
        f["column"] = filter_ui_cols[0].selectbox(f"Filter Column {i+1}", filter_columns_options, key=f"filter_col_{i}",
                                              index=filter_columns_options.index(current_filter_col_val) if current_filter_col_val in filter_columns_options else 0)
        
        selected_filter_column = f["column"]
        available_ops = ["==", "!=", "contains", "does not contain"]
        is_date_col_filter = False

        if selected_filter_column:
            # Check if the selected column for filtering is the designated date_col_for_filtering
            # OR if it's generally a date-like column in the source_df
            if selected_filter_column == date_col_for_filtering and date_col_for_filtering:
                 is_date_col_filter = True
            else:
                try:
                    if pd.api.types.is_datetime64_any_dtype(source_df_for_achievers[selected_filter_column]):
                        is_date_col_filter = True
                    else:
                        sample = source_df_for_achievers[selected_filter_column].dropna().iloc[:5]
                        if not sample.empty and pd.to_datetime(sample, errors='coerce').notna().all():
                            is_date_col_filter = True
                except Exception:
                    is_date_col_filter = False
            
            if is_date_col_filter:
                available_ops = ["is exactly", "is not", "is after", "is on or after",
                                 "is before", "is on or before", "is between (inclusive)",
                                 "is current month", "is previous month", "is next month",
                                 "is current year", "is previous year", "is next year"]
            elif pd.api.types.is_numeric_dtype(source_df_for_achievers[selected_filter_column]):
                available_ops = ["==", "!=", ">", "<", ">=", "<="]
        
        current_op_val = f["operator"]
        f["operator"] = filter_ui_cols[1].selectbox(f"Operator {i+1}", available_ops, key=f"filter_op_{i}",
                                                 index=available_ops.index(current_op_val) if current_op_val in available_ops else 0)

        # Value input based on operator and column type
        if is_date_col_filter and f["operator"] == "is between (inclusive)":
            val_start_key, val_end_key = f"filter_val_start_{i}", f"filter_val_end_{i}"
            if not isinstance(f["value"], list) or len(f["value"]) != 2:
                try:
                    # Attempt to convert column to datetime for min/max, use current date as fallback
                    dt_col_for_min_max = pd.to_datetime(source_df_for_achievers[selected_filter_column], errors='coerce')
                    min_val = dt_col_for_min_max.min()
                    max_val = dt_col_for_min_max.max()
                    if pd.isna(min_val): min_val = datetime.now().date()
                    if pd.isna(max_val): max_val = datetime.now().date()
                    f["value"] = [min_val, max_val]
                except Exception:
                     f["value"] = [datetime.now().date(), datetime.now().date()]

            f["value"][0] = filter_ui_cols[2].date_input("Start date", value=pd.to_datetime(f["value"][0], errors='coerce').date() if f["value"][0] else datetime.now().date(), key=val_start_key)
            f["value"][1] = filter_ui_cols[2].date_input("End date", value=pd.to_datetime(f["value"][1], errors='coerce').date() if f["value"][1] else datetime.now().date(), key=val_end_key)

        elif is_date_col_filter and f["operator"] in ["is exactly", "is not", "is after", "is on or after", "is before", "is on or before"]:
            default_date_val = pd.to_datetime(f["value"], errors='coerce')
            if pd.isna(default_date_val): default_date_val = datetime.now().date()
            else: default_date_val = default_date_val.date()
            f["value"] = filter_ui_cols[2].date_input(f"Date {i+1}", value=default_date_val, key=f"filter_val_date_{i}")
        elif is_date_col_filter and f["operator"] in ["is current month", "is previous month", "is next month", "is current year", "is previous year", "is next year"]:
            filter_ui_cols[2].markdown(f"*{f['operator']}* (no value needed)", unsafe_allow_html=True)
            f["value"] = None
        elif selected_filter_column and pd.api.types.is_numeric_dtype(source_df_for_achievers[selected_filter_column]):
            f["value"] = filter_ui_cols[2].number_input(f"Value {i+1}", value=pd.to_numeric(f["value"], errors='coerce'), key=f"filter_val_num_{i}")
        elif selected_filter_column and (pd.api.types.is_categorical_dtype(source_df_for_achievers[selected_filter_column]) or source_df_for_achievers[selected_filter_column].nunique() < 20):
            unique_vals = [""] + source_df_for_achievers[selected_filter_column].dropna().unique().tolist()
            current_f_val_cat = f["value"]
            f["value"] = filter_ui_cols[2].selectbox(f"Value {i+1}", options=unique_vals, key=f"filter_val_cat_{i}",
                                                  index=unique_vals.index(current_f_val_cat) if current_f_val_cat in unique_vals else 0)
        else:
            f["value"] = filter_ui_cols[2].text_input(f"Value {i+1}", value=str(f["value"]) if f["value"] is not None else "", key=f"filter_val_text_{i}")
        
        filter_ui_cols[3].button("➖", key=f"remove_filter_{i}", on_click=remove_filter, args=(i,))
    
    st.sidebar.button("Add Filter", on_click=add_filter)

    # Apply filters
    filtered_source_df = source_df_for_achievers.copy()
    if st.session_state.filters:
        for f_config in st.session_state.filters:
            if f_config["column"] and (f_config["value"] is not None or f_config["operator"] in ["is current month", "is previous month", "is next month", "is current year", "is previous year", "is next year"]): # Value can be None for relative date ops
                col = f_config["column"]
                op = f_config["operator"]
                val_config = f_config["value"]
                
                try:
                    col_data_for_op = filtered_source_df[col]
                    is_date_op_filter = op in ["is exactly", "is not", "is after", "is on or after", "is before", "is on or before", "is between (inclusive)", "is current month", "is previous month", "is next month", "is current year", "is previous year", "is next year"]
                    
                    if is_date_op_filter:
                        # Ensure the column used for date filtering is converted to datetime
                        date_col_to_filter = date_col_for_filtering if date_col_for_filtering == col else col
                        
                        col_data_dt = pd.to_datetime(filtered_source_df[date_col_to_filter], errors='coerce')
                        valid_date_mask = col_data_dt.notna()
                        if pd.api.types.is_datetime64_any_dtype(filtered_source_df[date_col_to_filter]):
                             valid_date_mask = valid_date_mask | filtered_source_df[date_col_to_filter].isna()
                        
                        temp_df_for_filter = filtered_source_df[valid_date_mask]
                        col_data_dt_for_filter = col_data_dt[valid_date_mask]

                        if op == "is between (inclusive)":
                            if isinstance(val_config, list) and len(val_config) == 2:
                                start_date, end_date = pd.to_datetime(val_config[0]), pd.to_datetime(val_config[1])
                                if not pd.isna(start_date) and not pd.isna(end_date) and start_date <= end_date:
                                    temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter.between(start_date, end_date, inclusive="both")]
                        elif op in ["is current month", "is previous month", "is next month", "is current year", "is previous year", "is next year"]:
                            today = pd.Timestamp.now().normalize()
                            if op == "is current month": temp_df_for_filter = temp_df_for_filter[(col_data_dt_for_filter.dt.year == today.year) & (col_data_dt_for_filter.dt.month == today.month)]
                            elif op == "is previous month":
                                current_month_start = today.replace(day=1)
                                prev_month_end = current_month_start - timedelta(days=1)
                                prev_month_start = prev_month_end.replace(day=1)
                                temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter.between(prev_month_start, prev_month_end, inclusive="both")]
                            elif op == "is next month":
                                current_month_end = today + pd.offsets.MonthEnd(0)
                                next_month_start = current_month_end + timedelta(days=1)
                                next_month_end = next_month_start + pd.offsets.MonthEnd(0)
                                temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter.between(next_month_start, next_month_end, inclusive="both")]
                            elif op == "is current year": temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter.dt.year == today.year]
                            elif op == "is previous year": temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter.dt.year == today.year - 1]
                            elif op == "is next year": temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter.dt.year == today.year + 1]
                        else: # Exact, after, before for dates
                            val_dt = pd.to_datetime(val_config, errors='coerce')
                            if not pd.isna(val_dt):
                                if op == "is exactly": temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter == val_dt]
                                elif op == "is not": temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter != val_dt]
                                elif op == "is after": temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter > val_dt]
                                elif op == "is on or after": temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter >= val_dt]
                                elif op == "is before": temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter < val_dt]
                                elif op == "is on or before": temp_df_for_filter = temp_df_for_filter[col_data_dt_for_filter <= val_dt]
                        filtered_source_df = temp_df_for_filter
                    else: # Non-date operations
                        val_str = str(val_config)
                        val = val_config
                        if pd.api.types.is_numeric_dtype(col_data_for_op) and op not in ["contains", "does not contain"]:
                            val = pd.to_numeric(val_str, errors='coerce')
                            if pd.isna(val): continue
                        elif op in ["contains", "does not contain"]:
                            col_data_str = col_data_for_op.astype(str)
                            if op == "contains": filtered_source_df = filtered_source_df[col_data_str.str.contains(val_str, case=False, na=False)]
                            elif op == "does not contain": filtered_source_df = filtered_source_df[~col_data_str.str.contains(val_str, case=False, na=False)]
                            continue
                        
                        if op == "==": filtered_source_df = filtered_source_df[col_data_for_op == val]
                        elif op == "!=": filtered_source_df = filtered_source_df[col_data_for_op != val]
                        elif op == ">": filtered_source_df = filtered_source_df[col_data_for_op > val]
                        elif op == "<": filtered_source_df = filtered_source_df[col_data_for_op < val]
                        elif op == ">=": filtered_source_df = filtered_source_df[col_data_for_op >= val]
                        elif op == "<=": filtered_source_df = filtered_source_df[col_data_for_op <= val]
                except Exception as e:
                    st.sidebar.warning(f"Could not apply filter on '{col}': {e}")
    
    # --- Generate Achievers List Button ---
    st.sidebar.header("4. Generate List")
    if st.sidebar.button("Generate Achievers List"):
        if not project_col or not sdr_col or not achieved_col:
            st.session_state.last_error = "Please select 'Project', 'SDR Name', and 'Achieved Value' columns."
        else:
            try:
                achievers_data = []
                for index, row in filtered_source_df.iterrows():
                    proj_name = row[project_col]
                    sdr_name = row[sdr_col] if sdr_col in row and pd.notna(row[sdr_col]) else ""
                    
                    try:
                        achieved_value = pd.to_numeric(row[achieved_col])
                        if pd.isna(achieved_value):
                            achieved_value = 0 # Treat non-numeric or missing achieved as 0
                    except ValueError:
                        achieved_value = 0 # Treat non-numeric achieved as 0


                    department_mapped = get_department_from_project(proj_name)
                    tier_a_val = get_tier_a_target(department_mapped)

                    achieved_percentage = 0.0
                    if tier_a_val is not None and tier_a_val > 0 and achieved_value is not None:
                        achieved_percentage = (achieved_value / tier_a_val) * 100
                    
                    achievers_data.append({
                        "Project": proj_name,
                        "SDR": sdr_name,
                        "Achieved": achieved_value,
                        "Tier A": tier_a_val if tier_a_val is not None else "N/A", # Show N/A if target not found
                        "Achieved%": achieved_percentage
                    })
                
                if achievers_data:
                    final_df = pd.DataFrame(achievers_data)
                    final_df = final_df.sort_values(by="Achieved%", ascending=False)
                    st.session_state.generated_list_df = final_df
                    st.session_state.last_success = "Achievers list generated successfully!"
                else:
                    st.session_state.generated_list_df = pd.DataFrame(columns=["Project", "SDR", "Achieved", "Tier A", "Achieved%"]) # Empty df
                    st.session_state.last_info = "No data to generate the list after filtering, or an issue occurred."


            except Exception as e:
                st.session_state.last_error = f"Error generating list: {e}"
                st.session_state.generated_list_df = None

# --- Display Generated List ---
if st.session_state.last_error and not st.session_state.generated_list_df: # Show error if list generation failed
    st.error(st.session_state.last_error)
    st.session_state.last_error = None

if st.session_state.last_success and st.session_state.generated_list_df is not None: # Show success if list generated
    st.success(st.session_state.last_success)
    st.session_state.last_success = None


if st.session_state.generated_list_df is not None:
    if not st.session_state.generated_list_df.empty:
        st.subheader("🚀 Achievers List")
        
        # Formatting the 'Achieved%' column
        display_df = st.session_state.generated_list_df.copy()
        display_df["Achieved%"] = display_df["Achieved%"].map('{:.2f}%'.format)
        if "Tier A" in display_df.columns: # Ensure Tier A is int or N/A
            display_df["Tier A"] = display_df["Tier A"].apply(lambda x: int(x) if isinstance(x, (int, float)) and pd.notna(x) and x == int(x) else x)
        if "Achieved" in display_df.columns:
             display_df["Achieved"] = display_df["Achieved"].apply(lambda x: int(x) if isinstance(x, (int, float)) and pd.notna(x) and x == int(x) else x)


        st.dataframe(display_df, use_container_width=True)

        st.subheader("Download Achievers List")
        @st.cache_data
        def convert_df_to_csv(df_to_convert):
            return df_to_convert.to_csv(index=False).encode('utf-8')

        csv_data = convert_df_to_csv(st.session_state.generated_list_df) # Download raw numbers for Achieved%
        
        achievers_filename = "achievers_list.csv"
        if st.session_state.uploaded_file_name:
            base_name = st.session_state.uploaded_file_name.rsplit('.', 1)[0]
            achievers_filename = f"achievers_{base_name}.csv"

        st.download_button(
            label="Download List as CSV",
            data=csv_data,
            file_name=achievers_filename,
            mime="text/csv"
        )
    elif hasattr(st.session_state, 'last_info') and st.session_state.last_info:
         st.info(st.session_state.last_info)
         st.session_state.last_info = None


elif st.session_state.achievers_df is not None:
    st.info("Configure column mappings and filters in the sidebar, then click 'Generate Achievers List'.")
elif not uploaded_file:
    st.info("👋 Welcome! Please upload a CSV file containing achievement data to get started.")