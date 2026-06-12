from ape import project, accounts

def main():
    # 使用本地测试链的默认账户（自动解锁）
    sender = accounts.test_accounts[0]
    
    # 部署合约，指定发送者
    contract = project.HelloWorld.deploy(sender=sender)
    print(f"✅ 合约部署成功！地址: {contract.address}")
    print(f"📤 部署账户: {sender.address}")
