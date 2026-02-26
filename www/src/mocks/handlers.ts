import { http, HttpResponse } from "msw";

const encoder = new TextEncoder();

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const randomDelay = (min: number, max: number) =>
  delay(Math.floor(Math.random() * (max - min + 1) + min));

const streamText = async (
  text: string,
  controller: ReadableStreamDefaultController,
) => {
  const words = text.split(" ");
  for (const word of words) {
    await randomDelay(10, 50); // Simulate variable typing speed
    controller.enqueue(encoder.encode(`${word} `));
  }
};

export const handlers = [
  http.post("/predict_stream", async ({ request }) => {
    // @ts-expect-error
    const { shouldError } = await request.json();

    await delay(1_000);

    const stream = new ReadableStream({
      async start(controller) {
        if (shouldError) {
          await delay(50);
          controller.error(new Error("Simulated error in stream"));
          return;
        }

        const content = `CoW Protocol provides infrastructure for trading (CoW Swap) and the Order Book API. Key points:

1. **Order Book API** – Programmatic order placement and quoting; use \`buyAmount\` with slippage for limit orders.

2. **Token approval** – You can set approval via ABI for gasless swaps; the API supports signing orders without transferring tokens first.

3. **Quoting** – Use "fast" for quick quotes or "optimal" when you want the best execution path.

4. **Errors** – InsufficientBalance usually means the solver cannot fulfill the order; check balance and slippage.

For more details see docs.cow.fi and the Order Book API documentation.`;

        await streamText(content, controller);

        await randomDelay(10, 100);
        controller.enqueue(encoder.encode("[DONE]\n"));
        controller.close();
      },
    });

    return new HttpResponse(stream, {
      headers: {
        "Content-Type": "text/plain",
      },
    });
  }),

  http.post("/predict", async ({ request }) => {
    // @ts-expect-error
    const { shouldError, memory, question } = await request.json();

    await delay(1_000);

    if (shouldError) {
      return new HttpResponse(
        JSON.stringify({ message: "Simulated error in stream" }),
        {
          status: 500,
          statusText: "Internal Server Error",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );
    }

    const response = {
      data: {
        answer:
          "To set buyAmount with slippage when creating an order, use the Order Book API quote endpoint to get a quote, then place an order with the desired limit. You can specify a slippage tolerance; the API returns valid order parameters. See the CoW Protocol integration docs at docs.cow.fi for exact request fields and examples.",
        url_supporting: [
          "https://docs.cow.fi/",
          "https://docs.cow.fi/docs/Integration/Order-book/order-creation",
        ],
      },
      error: null,
    };

    return new HttpResponse(JSON.stringify(response), {
      headers: {
        "Content-Type": "application/json",
      },
    });
  }),
];
