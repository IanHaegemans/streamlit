
import streamlit as st
import pandas as pd
import math
from io import BytesIO
from plotly import graph_objects as go
#import plotly.graph_objects as go


# Set up a green theme
st.set_page_config(
    page_title="Loan simulator",
    page_icon=":money_with_wings:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add some padding to the sidebar
st.markdown(
    """
    <style>
    .sidebar .sidebar-content {
        padding: 2rem 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.info('To get started with the loan calculator, enter your loan details below to create an Input Table on the right side of the screen. If either the Floating or Fixed interest rate is not applicable to your loan, simply set that interest rate to 0.', icon="ℹ️")
# Create a sidebar for user inputs
st.sidebar.title("Loan simulator")
Principal= st.sidebar.number_input("Enter the Principal Amount of the bond", value=4000000)
duration = st.sidebar.number_input("Enter the maturity of the bond (in years)", value=3)
interest_rate=st.sidebar.slider("Select a fixed interest rate in basis points ",0, 1500, step=5, format="%f", value= 200)
vinterest_rate=st.sidebar.slider("Select a Floating interest rate in basis points ",0, 1500, step=5, format="%f", value= 350)
vinterest_rate_periods = st.sidebar.selectbox("Select the reference/reset period for the Floating interest rate", ["12 months", "6 months", "3 months"])
payment_in_kind = st.sidebar.checkbox("Select if loan  type is 'Payment in kind', the interest due each year will increase the principal amount of the loan.")

hedgecosts= st.sidebar.number_input("Enter the cost of the hedging instrument if applicable", value=0)

# Calculate the number of periods per year based on Var_Interest_Rate type
if vinterest_rate_periods == "3 months":
    periods = 4
elif vinterest_rate_periods == "6 months":
    periods = 2
else:
    periods = 1

# Create a dataframe to store the Var_Interest_Rates for each period # if Prepayment is done at end of period this will substracted from the next Principal Amount period.
rates = pd.DataFrame(columns=["Year", "Period","Floating interest rate","Fixed interest rate", "Prepayment" ])
for i in range(duration * periods):
    rates.loc[i, "Year"] = math.ceil((i + 1) / periods)
    rates.loc[i, "Period"] = i + 1
    rates.loc[i, "Floating interest rate"] = vinterest_rate # Default Var_Interest_Rate
    rates.loc[i, "Fixed interest rate"]=interest_rate
    rates.loc[i, "Prepayment"]=0


# Allow the user to edit the Var_Interest_Rates with a data editor


st.header("Input Table")
rates = st.experimental_data_editor(rates)

expander = st.expander("Info Modifiable Variables")
expander.write('You can modify the variables for each period in the table above to suit your needs. For instance, you may want to simulate a higher Floating interest rate starting from year two. Simply make the changes to Floating interest rates starting from Year 2  in the Input Table and see how your loan will behave over time based on the new input')

expander = st.expander("Info Prepayment")
expander.write ('If you make a prepayment during a period, it will be applied at the end of that period. The prepayment will decrease the Principal Amount used for interest calculations starting from the next period. This means that the prepayment will have an impact on the total interest you will pay over the life of the loan. The loan calculator takes prepayments into account, helping you to see how different prepayment scenarios may affect your loan')
#Calculate the Principal Amount and Interest to be paid for each period and the total interest payment
rates["Principal Amount"] = Principal
rates["Interest added to Principal"]= 0
rates["Interest to be paid"] = 0
rates["Total_interest_rate"]=rates["Floating interest rate"]+ rates["Fixed interest rate"]
rates["Interest_due_to_Floating_interest_rate"] = 0
rates["Interest_due_to_Fixed interest rate"] = 0

# Use a Floating to store the annual Var_Interest_Rate
annual_rate = 0
annual_vrate=0
annual_frate=0


# Calculation interest rates
for i in range(len(rates)):
        # Add up the Total_interest_rate for each period within a year
        annual_rate += rates.loc[i, "Total_interest_rate"]/10000
        # Add up the Total_varaiblet_rate for each period within a year
        annual_vrate += rates.loc[i, "Floating interest rate"]/10000
        # Add up the Total_varaiblet_rate for each period within a year
        annual_frate += rates.loc[i, "Fixed interest rate"]/10000

        
        if i != 0:
            # make Principal Amount same to previous Principal Amount if it would be lower , see below:  if i < len(rates) - 1:
            rates.loc[i, "Principal Amount"]=rates.loc[i-1, "Principal Amount"]
            rates.loc[i, "Principal Amount"]=rates.loc[i, "Principal Amount"]+rates.loc[i-1,"Interest added to Principal"]
            rates.loc[i, "Principal Amount"]=rates.loc[i, "Principal Amount"]-rates.loc[i-1,"Prepayment"]
        # Check if the end of the year is reached
        if (i + 1) % periods == 0:
            # Calculate the Interest to be paid based on the annual rate (= annual rate/periods) and the Principal Amount
            rates.loc[i, "Interest to be paid"] = rates.loc[i,"Principal Amount"] * (annual_rate/periods)

            rates.loc[i, "Interest_due_to_Floating_interest_rate"] = rates.loc[i,"Principal Amount"] * (annual_vrate/periods)

            rates.loc[i, "Interest_due_to_Fixed interest rate"] = rates.loc[i,"Principal Amount"] * (annual_frate/periods)
            
            # Add the Interest to be paid to the Principal Amount for the next year, unless it is the last period.
            if i < len(rates) - 1:

                if payment_in_kind:
                # Add to interest_added_to_notinal and make  Interest to be paid 0 again
                    rates.loc[i, "Interest added to Principal"]= rates.loc[i, "Interest to be paid"]
                    rates.loc[i, "Interest to be paid"]=0
            # Reset the annual rate to zero for the next yea
                annual_rate = 0
                annual_vrate=0
                annual_frate=0


# Show the Net cash outflows at the end of each year
rates["Net cash outflow"] = 0
for i in range(len(rates)):
    if (i + 1) % periods == 0: # End of year
        if i == len(rates) - 1: # Maturity date
                rates.loc[i, "Net cash outflow"] = rates.loc[i, "Principal Amount"]+rates.loc[i, "Interest to be paid"]+rates.loc[i,"Prepayment"]
        else: # Cash payment every year
            rates.loc[i, "Net cash outflow"] = rates.loc[i, "Interest to be paid"]+rates.loc[i,"Prepayment"]

#total interest payments
total_net_cost = rates['Net cash outflow'].sum()-Principal+hedgecosts


totalvinterest = rates["Interest_due_to_Floating_interest_rate"].sum()

totalfinterest = rates["Interest_due_to_Fixed interest rate"].sum()
# Display the table with the results
# Display the results
st.header(" Output: Summary results")

#format correctly
formatted_total_net_cost = "{:,}".format(total_net_cost)
formatted_totalvinterest = "{:,}".format(totalvinterest)
formatted_totalfinterest = "{:,}".format(totalfinterest)
formatted_hedgecosts = "{:,}".format(hedgecosts)

st.write(f"The number of reference periods per year is {periods}")
st.write(f"The total net cost is {formatted_total_net_cost} with {formatted_totalvinterest} from the Floating {formatted_totalfinterest} from the Fixed interest rate and {formatted_hedgecosts} from the hedging instrument ")
st.write(f"The payment in kind option is {'enabled' if payment_in_kind else 'disabled'}")
# Create a new dataframe to store only the rows for the last period in the year
last_period_df = pd.DataFrame(columns=rates.columns)

for i in range(len(rates)):
    # Check if the current row is the last period in the year
    if (i + 1) % periods == 0:
        # Add the row to the last_period_df dataframe
        last_period_df = pd.concat([last_period_df, rates.iloc[[i]]])

# Create a new DataFrame with only the relevant columns
last_period_df_relevant = last_period_df[["Year", "Principal Amount", "Interest added to Principal", "Interest to be paid","Net cash outflow"]]

# Display the DataFrame using st.write
st.write(last_period_df_relevant)


# Create a trace for each data series
trace1 = go.Scatter(x=last_period_df["Year"], y=last_period_df["Principal Amount"], mode='markers', name="Principal Amount", 
                 marker=dict(size=10))
trace2 = go.Scatter(x=last_period_df["Year"], y=last_period_df["Interest added to Principal"], mode='markers', 
                    name="Interest added to Principal", marker=dict(size=10))


trace3 = go.Scatter(x=last_period_df["Year"], y=last_period_df["Interest_due_to_Floating_interest_rate"], mode='markers', 
                    name="Interest due to Floating interest rate", marker=dict(size=10))

trace4 = go.Scatter(x=last_period_df["Year"], y=last_period_df["Interest_due_to_Fixed interest rate"], mode='markers', 
                    name="Interest due to fixed interest rate", marker=dict(size=10))

trace5 = go.Scatter(x=last_period_df["Year"], y=last_period_df["Net cash outflow"], mode='markers', name="Net cash outflow", 
                    marker=dict(size=10))

# Create a layout with title and axis labels
layout = go.Layout(title="Interest and Cash flows over time", xaxis=dict(title="year", tickmode='array', tick0=last_period_df["Principal Amount"].iloc[0]), 
                   yaxis=dict(title="Amount"))

# Combine the traces and layout into a figure
fig = go.Figure(data=[trace1, trace2, trace3, trace4, trace5], layout=layout)

# Display the figure
st.plotly_chart(fig)

st.header(" Output: Detailed results per period")

# Allow the user to select which columns to display
columns = st.multiselect("Select columns to display", rates.columns)


# Display the rates dataframe with the selected columns
st.write(rates[columns])


# Downloud as excel
def to_excel(df):
  output = BytesIO()
  with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name='Sheet1')
  processed_data = output.getvalue()
  return processed_data

df_xlsx = to_excel(rates)
st.download_button(
  label='Download data as Excel',
  data=df_xlsx,
  file_name='data_bond.xlsx',
  mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

