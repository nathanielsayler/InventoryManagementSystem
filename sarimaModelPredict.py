import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
import plotly.graph_objs as go
from plotly.offline import plot

def create_forecast_plot_html(data_input):
    #Load and preprocess data
    data = pd.DataFrame(data_input)

    data['qty_sold'] = data['quantity']
    data['Date'] = pd.to_datetime(data['date_sold'], format='%m-%d-%Y')
    data.set_index('Date', inplace=True)

    #Resampling data to the weekly level from daily input
    data['qty_sold'].fillna(method='ffill', inplace=True)
    weekly_data = data['qty_sold'].resample('W').sum().iloc[1:]

    #Defining and fit the SARIMA model
    model = SARIMAX(
        weekly_data,
        order=(1, 1, 1),           # Non-seasonal parameters (p=1, d=1, q=1)
        seasonal_order=(1, 1, 1, 52)  # Seasonal parameters with yearly period
    )
    model_fit = model.fit(disp=False)

    #Forecast the next 52 weeks (1 year)
    forecast_log = model_fit.get_forecast(steps=52)
    forecast_mean = forecast_log.predicted_mean

    #Creating a Plotly figure
    fig = go.Figure()

    #Populating historical data on the chart
    fig.add_trace(go.Scatter(
        x=weekly_data.index, y=weekly_data,
        mode='lines', name='Observed',
        line=dict(color='blue')
    ))

    #Populating forecasted data on the chart
    fig.add_trace(go.Scatter(
        x=forecast_mean.index, y=forecast_mean,
        mode='lines', name='Forecast',
        line=dict(color='red', dash='dash')
    ))

    #Adding a vertical line to separate historical data and forecasted data
    fig.add_shape(
        type="line", x0=weekly_data.index[-1], x1=weekly_data.index[-1],
        y0=min(weekly_data.min(), forecast_mean.min()), y1=max(weekly_data.max(), forecast_mean.max()),
        line=dict(color="Gray", width=2, dash="dashdot")
    )

    #Adding title, axis titles, and legend
    fig.update_layout(
        title="Sales Forecast using SARIMA Model with Yearly Seasonality",
        xaxis_title="Date",
        yaxis_title="Quantity Sold",
        showlegend=True
    )

    #Rendering in html so the plot can be viewed in browser
    plot_html = plot(fig, output_type='div')  # Save the plot to a variable as HTML code
    return plot_html


def generate_profit_report(data_input):
    data = pd.DataFrame(data_input)

    data['Date'] = pd.to_datetime(data['date_sold'], format='%m-%d-%Y')
    data['Month'] = data['Date'].dt.to_period('M')  # Convert to monthly period

    data['Revenue'] = data['quantity'] * data['sale_price']
    data['Cost'] = data['quantity'] * data['acquisition_cost']

    #Calculate monthly profit and margin
    monthly_data = data.groupby('Month').agg(
        Revenue=('Revenue', 'sum'),
        Cost=('Cost', 'sum')
    ).reset_index()

    monthly_data['Profit'] = monthly_data['Revenue'] - monthly_data['Cost']
    monthly_data['Margin'] = (monthly_data['Profit'] / monthly_data['Revenue']) * 100  # Margin as percentage

    #Convert 'Month' back to datetime to pass into Plotly
    monthly_data['Month'] = monthly_data['Month'].dt.to_timestamp()

    #Creating Profit Bar Chart
    profit_fig = go.Figure()

    profit_fig.add_trace(go.Bar(
        x=monthly_data['Month'],
        y=monthly_data['Profit'],
        name='Profit',
        marker=dict(color='blue'),
        text=monthly_data['Profit'].round(1),
        textposition='auto'
    ))

    profit_fig.update_layout(
        title="Monthly Profit",
        xaxis_title="Month",
        yaxis_title="Profit ($)",
        template="plotly_white"
    )

    #Creating Margin Line Chart with Data Labels
    margin_fig = go.Figure()

    margin_fig.add_trace(go.Scatter(
        x=monthly_data['Month'],
        y=monthly_data['Margin'],
        name='Margin (%)',
        mode='lines+markers',
        text=monthly_data['Margin'].round(1).astype(str) + '%',
        textposition='top center',
        marker=dict(color='red'),
        line=dict(color='red', width=2)
    ))

    margin_fig.update_layout(
        title="Monthly Margin",
        xaxis_title="Month",
        yaxis_title="Margin (%)",
        template="plotly_white"
    )


    #Combining the two charts into a single html output
    profit_html = plot(profit_fig, output_type='div')
    margin_html = plot(margin_fig, output_type='div')
    combined_html = f"{profit_html}<br><br>{margin_html}"

    return combined_html


def generate_inventory_history(current_inventory, inventory_history):
    transactions_df = pd.DataFrame(inventory_history)

    #Summing current quantities
    current_quantity = sum(record['quantity'] for record in current_inventory)

    #Calculating monthly deltas from transactions
    transactions_df['date'] = pd.to_datetime(transactions_df['date'])
    transactions_df['month'] = transactions_df['date'].dt.to_period('M')
    monthly_deltas = transactions_df.groupby('month').qty_change.sum().reset_index()

    #Generating monthly inventory levels
    min_month = transactions_df['month'].min()
    max_month = transactions_df['month'].max()
    all_months = pd.period_range(min_month, max_month, freq='M')
    monthly_inventory = pd.DataFrame(all_months, columns=['month'])

    #Merge with monthly deltas and fill missing changes with 0
    monthly_inventory = monthly_inventory.merge(monthly_deltas, on='month', how='left')
    monthly_inventory['qty_change'] = monthly_inventory['qty_change'].fillna(0)

    #Calculate cumulative inventory starting from the current quantity
    monthly_inventory = monthly_inventory.sort_values('month', ascending=False)  # Start with the most recent month
    monthly_inventory['actual_inventory'] = current_quantity - monthly_inventory['qty_change'].cumsum()

    #Convert month to datetime to pass into Plotly
    monthly_inventory['month'] = monthly_inventory['month'].dt.to_timestamp()

    #Creating a Plotly bar chart
    fig = go.Figure()

    #Adding barchart with inventory levels
    fig.add_trace(go.Bar(
        x=monthly_inventory['month'],  # Use datetime month for proper alignment
        y=monthly_inventory['actual_inventory'],
        name='Inventory Level'
    ))

    #Adding title, axis titles
    fig.update_layout(
        title="Monthly Inventory Levels",
        xaxis_title="Month",
        yaxis_title="Inventory Level",
        template="plotly_white",
        xaxis=dict(
            tickvals=monthly_inventory['month'],  # Set ticks at each month
            ticktext=monthly_inventory['month'].dt.strftime('%b %Y'),  # Display only month and year
            tickmode="array"  # Ensure only specified ticks appear
        )
    )

    #render to html to pass into Flask app
    plot_html = plot(fig, output_type='div')
    return plot_html
