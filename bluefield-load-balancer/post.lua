wrk.method = "POST"
wrk.body = '{"flow_id": ' .. math.random(1, 100000) .. '}'
wrk.headers["Content-Type"] = "application/json"
